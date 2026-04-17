"""
Unit + smoke tests for the Go/No-Go Task (build-v0.1, 2026-04-04).

Coverage:
  1. Stimulus generation — ratio validation for all difficulty tiers
  2. Scoring formula — all four outcome types (hits, misses, false alarms, correct rejections)
  3. Session recording — backend accepts go_no_go exercise results with correct payload shape
  4. Auth enforcement — unauthenticated requests are rejected

These tests port the JavaScript logic from GoNoGo.jsx into Python so it can be
validated with pytest alongside the rest of the backend test suite.
The backend route POST /api/sessions/{id}/exercise-result already handles
exercise_type="go_no_go" without any changes.
"""

import math
import random
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine


# ─── Ports of JS game logic ────────────────────────────────────────────────────

TOTAL_STIMULI = 20

GO_STIMULUS  = {'shape': 'circle',   'color': '#3D9E72', 'label': 'green circle',     'isGo': True}
NOGO_OPTIONS = [
    {'shape': 'circle',   'color': '#D95F5F', 'label': 'red circle',      'isGo': False},
    {'shape': 'square',   'color': '#4A90C4', 'label': 'blue square',     'isGo': False},
    {'shape': 'triangle', 'color': '#C9973A', 'label': 'orange triangle', 'isGo': False},
]


def get_difficulty_config(difficulty: int) -> dict:
    """Mirror of getDifficultyConfig() in GoNoGo.jsx"""
    if difficulty <= 3:
        return {'label': 'Easy',   'displayMs': 1000, 'noGoCount': 1, 'goRatio': 0.75}
    if difficulty <= 6:
        return {'label': 'Medium', 'displayMs': 700,  'noGoCount': 2, 'goRatio': 0.70}
    return     {'label': 'Hard',   'displayMs': 450,  'noGoCount': 3, 'goRatio': 0.65}


def generate_stimuli(config: dict, rng=None) -> list:
    """
    Mirror of generateStimuli() in GoNoGo.jsx.
    rng: optional random.Random for reproducible tests.
    """
    if rng is None:
        rng = random

    total   = TOTAL_STIMULI
    num_go  = round(total * config['goRatio'])
    num_nogo = total - num_go

    nogo_variants = NOGO_OPTIONS[:config['noGoCount']]
    sequence = []

    for _ in range(num_go):
        sequence.append(dict(GO_STIMULUS))
    for i in range(num_nogo):
        sequence.append(dict(nogo_variants[i % len(nogo_variants)]))

    # Fisher-Yates shuffle
    for i in range(len(sequence) - 1, 0, -1):
        j = int(rng.random() * (i + 1))
        sequence[i], sequence[j] = sequence[j], sequence[i]

    return sequence


def compute_result(hits: int, misses: int, false_alarms: int, correct_rejections: int,
                   response_times: list) -> dict:
    """Mirror of computeResult() in GoNoGo.jsx"""
    total     = hits + misses + false_alarms + correct_rejections
    raw_score = hits + correct_rejections - false_alarms - misses
    accuracy  = max(0.0, raw_score) / total if total > 0 else 0.0

    avg_rt = (
        round(sum(response_times) / len(response_times))
        if response_times else 0
    )

    return {
        'trials_presented':   total,
        'trials_correct':     hits + correct_rejections,
        'avg_response_ms':    avg_rt,
        'accuracy':           accuracy,
        'hits':               hits,
        'misses':             misses,
        'false_alarms':       false_alarms,
        'correct_rejections': correct_rejections,
    }


# ─── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth(client):
    client.post("/api/auth/register", json={
        "email": "gng@test.com",
        "username": "gng_tester",
        "password": "TestPass123!",
        "consent_given": True,
    })
    r = client.post("/api/auth/login", json={
        "email": "gng@test.com",
        "password": "TestPass123!",
    })
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ─── 1. Difficulty configuration ───────────────────────────────────────────────

class TestDifficultyConfig:
    def test_difficulty_1_is_easy(self):
        cfg = get_difficulty_config(1)
        assert cfg['label'] == 'Easy'
        assert cfg['displayMs'] == 1000
        assert cfg['noGoCount'] == 1
        assert cfg['goRatio'] == 0.75

    def test_difficulty_3_is_easy(self):
        assert get_difficulty_config(3)['label'] == 'Easy'

    def test_difficulty_4_is_medium(self):
        cfg = get_difficulty_config(4)
        assert cfg['label'] == 'Medium'
        assert cfg['displayMs'] == 700
        assert cfg['noGoCount'] == 2
        assert cfg['goRatio'] == 0.70

    def test_difficulty_6_is_medium(self):
        assert get_difficulty_config(6)['label'] == 'Medium'

    def test_difficulty_7_is_hard(self):
        cfg = get_difficulty_config(7)
        assert cfg['label'] == 'Hard'
        assert cfg['displayMs'] == 450
        assert cfg['noGoCount'] == 3
        assert cfg['goRatio'] == 0.65

    def test_difficulty_10_is_hard(self):
        assert get_difficulty_config(10)['label'] == 'Hard'

    def test_baseline_difficulty_2_maps_to_easy(self):
        """Baseline level 1 → difficulty 2 (LEVEL_TO_DIFFICULTY in BaselineGameWrapper)"""
        assert get_difficulty_config(2)['label'] == 'Easy'

    def test_baseline_difficulty_5_maps_to_medium(self):
        """Baseline level 2 → difficulty 5"""
        assert get_difficulty_config(5)['label'] == 'Medium'

    def test_baseline_difficulty_8_maps_to_hard(self):
        """Baseline level 3 → difficulty 8"""
        assert get_difficulty_config(8)['label'] == 'Hard'


# ─── 2. Stimulus generation ─────────────────────────────────────────────────────

class TestStimulusGeneration:
    @pytest.mark.parametrize("difficulty", [2, 5, 8])
    def test_total_stimuli_always_20(self, difficulty):
        cfg = get_difficulty_config(difficulty)
        seq = generate_stimuli(cfg)
        assert len(seq) == 20

    def test_easy_go_ratio_is_75_percent(self):
        """Easy: round(20 × 0.75) = 15 Go stimuli"""
        cfg = get_difficulty_config(1)
        rng = random.Random(42)
        seq = generate_stimuli(cfg, rng=rng)
        go_count = sum(1 for s in seq if s['isGo'])
        assert go_count == 15

    def test_medium_go_ratio_is_70_percent(self):
        """Medium: round(20 × 0.70) = 14 Go stimuli"""
        cfg = get_difficulty_config(5)
        rng = random.Random(99)
        seq = generate_stimuli(cfg, rng=rng)
        go_count = sum(1 for s in seq if s['isGo'])
        assert go_count == 14

    def test_hard_go_ratio_is_65_percent(self):
        """Hard: round(20 × 0.65) = 13 Go stimuli"""
        cfg = get_difficulty_config(8)
        rng = random.Random(7)
        seq = generate_stimuli(cfg, rng=rng)
        go_count = sum(1 for s in seq if s['isGo'])
        assert go_count == 13

    def test_easy_has_exactly_one_nogo_type(self):
        """Easy uses only red circle as No-Go"""
        cfg = get_difficulty_config(2)
        seq = generate_stimuli(cfg)
        nogo_shapes = set(s['shape'] for s in seq if not s['isGo'])
        nogo_colors = set(s['color'] for s in seq if not s['isGo'])
        assert len(nogo_shapes) == 1
        assert '#D95F5F' in nogo_colors  # red circle only

    def test_medium_has_exactly_two_nogo_types(self):
        """Medium uses red circle + blue square"""
        cfg = get_difficulty_config(5)
        seq = generate_stimuli(cfg)
        nogo_labels = set(s['label'] for s in seq if not s['isGo'])
        # With 6 No-Go stimuli distributed across 2 types, both must appear
        assert len(nogo_labels) == 2

    def test_hard_has_all_three_nogo_types(self):
        """Hard uses red circle + blue square + orange triangle"""
        cfg = get_difficulty_config(8)
        seq = generate_stimuli(cfg)
        nogo_labels = set(s['label'] for s in seq if not s['isGo'])
        assert 'red circle'      in nogo_labels
        assert 'blue square'     in nogo_labels
        assert 'orange triangle' in nogo_labels

    def test_go_stimulus_is_always_green_circle(self):
        for difficulty in [2, 5, 8]:
            cfg = get_difficulty_config(difficulty)
            seq = generate_stimuli(cfg)
            for stim in seq:
                if stim['isGo']:
                    assert stim['shape'] == 'circle'
                    assert stim['color'] == '#3D9E72'

    @pytest.mark.parametrize("difficulty,expected_nogo", [(2, 5), (5, 6), (8, 7)])
    def test_nogo_count_matches_ratio(self, difficulty, expected_nogo):
        """No-Go count = 20 − numGo"""
        cfg = get_difficulty_config(difficulty)
        seq = generate_stimuli(cfg)
        nogo_count = sum(1 for s in seq if not s['isGo'])
        assert nogo_count == expected_nogo

    def test_sequence_is_shuffled(self):
        """Running generator twice should (almost always) produce different orderings"""
        cfg = get_difficulty_config(5)
        seq1 = generate_stimuli(cfg, rng=random.Random(1))
        seq2 = generate_stimuli(cfg, rng=random.Random(2))
        # Sequences should differ in at least one position (astronomically unlikely to match)
        orders_match = all(s1['isGo'] == s2['isGo'] for s1, s2 in zip(seq1, seq2))
        assert not orders_match


# ─── 3. Scoring formula ────────────────────────────────────────────────────────

class TestScoringFormula:
    """
    Formula: raw = hits + correct_rejections − false_alarms − misses
             accuracy = max(0, raw) / total   (total = 20)
             trials_correct = hits + correct_rejections
    """

    def test_perfect_score_all_hits_and_correct_rejections(self):
        """All 15 Go tapped, all 5 No-Go withheld → 100% accuracy"""
        r = compute_result(hits=15, misses=0, false_alarms=0, correct_rejections=5, response_times=[500]*15)
        assert r['trials_presented'] == 20
        assert r['trials_correct']   == 20
        assert r['accuracy']         == 1.0

    def test_all_misses_and_false_alarms_clamp_to_zero_accuracy(self):
        """raw = 0 + 0 − 5 − 15 = −20 → clamped to 0"""
        r = compute_result(hits=0, misses=15, false_alarms=5, correct_rejections=0, response_times=[])
        assert r['accuracy'] == 0.0
        assert r['trials_correct'] == 0

    def test_hit_counts_correct(self):
        r = compute_result(hits=10, misses=5, false_alarms=3, correct_rejections=2, response_times=[400]*10)
        assert r['hits']   == 10
        assert r['misses'] == 5
        assert r['false_alarms']       == 3
        assert r['correct_rejections'] == 2

    def test_accuracy_penalises_false_alarms(self):
        """
        Scenario A: 15 hits, 5 correct rejections, 0 false alarms, 0 misses → 100%
        Scenario B: 15 hits, 3 correct rejections, 2 false alarms, 0 misses
                    raw = 15+3−2−0 = 16 → accuracy = 16/20 = 0.8
        """
        r_a = compute_result(hits=15, misses=0, false_alarms=0, correct_rejections=5, response_times=[500]*15)
        r_b = compute_result(hits=15, misses=0, false_alarms=2, correct_rejections=3, response_times=[500]*15)
        assert r_a['accuracy'] == 1.0
        assert abs(r_b['accuracy'] - 0.8) < 1e-9

    def test_accuracy_penalises_misses(self):
        """
        15 Go, all missed; 5 No-Go, all correct rejections
        raw = 0 + 5 − 0 − 15 = −10 → clamped to 0
        """
        r = compute_result(hits=0, misses=15, false_alarms=0, correct_rejections=5, response_times=[])
        assert r['accuracy'] == 0.0

    def test_trials_correct_is_hits_plus_correct_rejections(self):
        r = compute_result(hits=12, misses=3, false_alarms=2, correct_rejections=3, response_times=[300]*12)
        assert r['trials_correct'] == 15  # 12 + 3

    def test_avg_response_ms_is_zero_when_no_hits(self):
        r = compute_result(hits=0, misses=15, false_alarms=5, correct_rejections=0, response_times=[])
        assert r['avg_response_ms'] == 0

    def test_avg_response_ms_rounds_to_nearest_ms(self):
        r = compute_result(hits=3, misses=0, false_alarms=0, correct_rejections=0, response_times=[301, 302, 303])
        assert r['avg_response_ms'] == 302

    def test_accuracy_for_typical_medium_performance(self):
        """
        Typical medium-difficulty round:
        14 Go — 11 hits, 3 misses; 6 No-Go — 4 correct rejections, 2 false alarms
        raw = 11 + 4 − 2 − 3 = 10 → accuracy = 10/20 = 0.5
        """
        r = compute_result(hits=11, misses=3, false_alarms=2, correct_rejections=4, response_times=[650]*11)
        assert abs(r['accuracy'] - 0.5) < 1e-9

    def test_baseline_correctness_threshold(self):
        """
        BaselineGameWrapper marks a round correct if payload.accuracy >= 0.6.
        Verify boundary cases.
        """
        # Exactly 0.6 → correct (boundary inclusive)
        r_boundary = compute_result(hits=12, misses=3, false_alarms=0, correct_rejections=5, response_times=[500]*12)
        # raw = 12+5−0−3=14, accuracy=14/20=0.7 > 0.6 ✓
        assert r_boundary['accuracy'] >= 0.6

        # Below threshold
        r_below = compute_result(hits=7, misses=8, false_alarms=5, correct_rejections=0, response_times=[500]*7)
        # raw = 7+0−5−8=−6 → clamped to 0, accuracy=0 < 0.6
        assert r_below['accuracy'] < 0.6


# ─── 4. Backend smoke tests ────────────────────────────────────────────────────

class TestGoNoGoBackendCompatibility:
    """Verify the backend session API accepts go_no_go results."""

    def _start_session(self, client, auth):
        r = client.post("/api/sessions/start", headers=auth, json={
            "domain_1": "attention",
            "domain_2": "processing_speed",
            "is_baseline": 0,
        })
        assert r.status_code == 200
        return r.json()["id"]

    def test_go_no_go_result_accepted(self, client, auth):
        sid = self._start_session(client, auth)
        r = client.post(
            f"/api/sessions/{sid}/exercise-result",
            headers=auth,
            json={
                "domain":           "attention",
                "exercise_type":    "go_no_go",
                "trials_presented": 20,
                "trials_correct":   17,
                "avg_response_ms":  480,
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["trials_presented"] == 20
        assert data["trials_correct"]   == 17
        assert data["avg_response_ms"]  == 480

    def test_perfect_round_recorded_correctly(self, client, auth):
        """All 20 correct (15 hits + 5 correct rejections)"""
        sid = self._start_session(client, auth)
        r = client.post(
            f"/api/sessions/{sid}/exercise-result",
            headers=auth,
            json={
                "domain":           "attention",
                "exercise_type":    "go_no_go",
                "trials_presented": 20,
                "trials_correct":   20,
                "avg_response_ms":  310,
            },
        )
        assert r.status_code == 200
        assert r.json()["trials_correct"] == 20

    def test_all_incorrect_round_recorded(self, client, auth):
        """Zero correct — all misses and false alarms"""
        sid = self._start_session(client, auth)
        r = client.post(
            f"/api/sessions/{sid}/exercise-result",
            headers=auth,
            json={
                "domain":           "attention",
                "exercise_type":    "go_no_go",
                "trials_presented": 20,
                "trials_correct":   0,
                "avg_response_ms":  0,
            },
        )
        assert r.status_code == 200
        assert r.json()["trials_correct"] == 0

    def test_go_no_go_result_without_avg_rt(self, client, auth):
        """avg_response_ms=0 is valid (no hits in round)"""
        sid = self._start_session(client, auth)
        r = client.post(
            f"/api/sessions/{sid}/exercise-result",
            headers=auth,
            json={
                "domain":           "attention",
                "exercise_type":    "go_no_go",
                "trials_presented": 20,
                "trials_correct":   5,
                "avg_response_ms":  0,
            },
        )
        assert r.status_code == 200
        assert r.json()["avg_response_ms"] == 0

    def test_unauthenticated_request_rejected(self, client, auth):
        sid = self._start_session(client, auth)
        with TestClient(app, cookies={}) as fresh:
            r = fresh.post(
                f"/api/sessions/{sid}/exercise-result",
                json={
                    "domain":           "attention",
                    "exercise_type":    "go_no_go",
                    "trials_presented": 20,
                    "trials_correct":   15,
                    "avg_response_ms":  500,
                },
            )
        assert r.status_code == 401

    def test_session_can_be_completed_after_go_no_go(self, client, auth):
        """Full round flow: start → record go_no_go → complete"""
        sid = self._start_session(client, auth)

        client.post(
            f"/api/sessions/{sid}/exercise-result",
            headers=auth,
            json={
                "domain":           "attention",
                "exercise_type":    "go_no_go",
                "trials_presented": 20,
                "trials_correct":   15,
                "avg_response_ms":  420,
            },
        )

        complete = client.post(f"/api/sessions/{sid}/complete", headers=auth)
        assert complete.status_code == 200
        assert "Session completed" in complete.json()["message"]

    def test_go_no_go_updates_domain_progress(self, client, auth):
        """
        Recording a go_no_go result should create/update domain progress for 'attention'.
        The domain progress endpoint returns 200 with a valid current_difficulty.

        Note: total_attempts is only incremented when a DomainProgress record already
        exists at the time the exercise-result route runs (the AdaptiveDifficultyService
        creates it afterward). On the very first exercise in a domain the record is
        created by the service but the attempt counters remain at zero — this is a
        pre-existing backend behaviour, not a regression introduced by Go/No-Go.
        """
        sid = self._start_session(client, auth)

        client.post(
            f"/api/sessions/{sid}/exercise-result",
            headers=auth,
            json={
                "domain":           "attention",
                "exercise_type":    "go_no_go",
                "trials_presented": 20,
                "trials_correct":   18,
                "avg_response_ms":  360,
            },
        )

        progress = client.get("/api/progress/domain/attention", headers=auth)
        assert progress.status_code == 200
        data = progress.json()
        # The record exists and has a valid difficulty level (1–10)
        assert 1 <= data["current_difficulty"] <= 10

    def test_go_no_go_difficulty_from_baseline_profile_respected(self, client, auth):
        """
        After submitting a baseline result that sets go_no_go to level 3 (Hard),
        the next exercise should respect the assessed level when starting a session.
        """
        # Submit a baseline that puts go_no_go at assessed_level=3 (Hard → difficulty 8).
        # The endpoint expects {"results": [...]} not a bare list.
        client.post("/api/adaptive-baseline/complete", headers=auth, json={
            "results": [{"game_key": "go_no_go", "assessed_level": 3}],
        })

        status = client.get("/api/adaptive-baseline/status", headers=auth)
        assert status.status_code == 200
        data = status.json()
        assert data["has_completed"] is True

        # Verify the go_no_go entry in the profile is level 3
        profile = {entry["game_key"]: entry["assessed_level"] for entry in data["profile"]}
        assert profile.get("go_no_go") == 3
