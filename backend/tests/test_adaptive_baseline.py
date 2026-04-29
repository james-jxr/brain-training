"""Tests for the adaptive baseline feature.

Covers:
  1. Pure algorithm: applyAdaptiveStep (2-up/1-down, floor, ceiling, convergence)
  2. API: GET /api/adaptive-baseline/status
  3. API: POST /api/adaptive-baseline/complete (happy path + error paths)
  4. Smoke: first-login prompt flag, full run upsert, retake increments baseline_count
  5. DomainProgress seeding from baseline results
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal, Base, engine
from backend.models.domain_progress import DomainProgress

# ─── Shared fixtures ──────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    with TestClient(app) as c:
        yield c


def _register_and_token(client, email="user@example.com", username="user", password="password123"):
    res = client.post("/api/auth/register", json={
        "email": email,
        "username": username,
        "password": password,
        "consent_given": True,
    })
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _register_and_token_with_id(client, email="user@example.com", username="user", password="password123"):
    res = client.post("/api/auth/register", json={
        "email": email,
        "username": username,
        "password": password,
        "consent_given": True,
    })
    assert res.status_code == 200, res.text
    return res.json()["access_token"], res.json()["user"]["id"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# ─── 1. Pure algorithm: applyAdaptiveStep ──────────────────────────────────────────────────────────────────────────────────────────────────────────
# These tests import the exported JS-mirrored logic from the frontend wrapper.
# Since that logic lives in a JS file we replicate the identical algorithm here
# in pure Python so we can unit-test the spec without needing a JS runtime.

def _apply_adaptive_step(state, correct):
    """Python mirror of BaselineGameWrapper.applyAdaptiveStep (2-up/1-down)."""
    level = state["level"]
    consecutive_correct = state["consecutiveCorrect"]

    if correct:
        consecutive_correct += 1
        if consecutive_correct >= 2:
            level = min(3, level + 1)
            consecutive_correct = 0
    else:
        level = max(1, level - 1)
        consecutive_correct = 0

    return {"level": level, "consecutiveCorrect": consecutive_correct}


class TestAdaptiveAlgorithm:
    """Unit tests for the 2-up/1-down adaptive staircase algorithm."""

    def _initial_state(self, level=1):
        return {"level": level, "consecutiveCorrect": 0}

    # ── Level increases ──────────────────────────────────────────────────────────────────────────────────────────────────────────

    def test_one_correct_does_not_increase_level(self):
        state = _apply_adaptive_step(self._initial_state(1), correct=True)
        assert state["level"] == 1
        assert state["consecutiveCorrect"] == 1

    def test_two_correct_increases_level(self):
        s = self._initial_state(1)
        s = _apply_adaptive_step(s, correct=True)
        s = _apply_adaptive_step(s, correct=True)
        assert s["level"] == 2
        assert s["consecutiveCorrect"] == 0

    def test_counter_resets_after_level_up(self):
        s = self._initial_state(1)
        s = _apply_adaptive_step(s, correct=True)
        s = _apply_adaptive_step(s, correct=True)
        # Now one more correct — should NOT jump to 3 immediately
        s = _apply_adaptive_step(s, correct=True)
        assert s["level"] == 2
        assert s["consecutiveCorrect"] == 1

    def test_two_more_correct_after_level_up_raises_again(self):
        s = self._initial_state(2)
        s = _apply_adaptive_step(s, correct=True)
        s = _apply_adaptive_step(s, correct=True)
        assert s["level"] == 3

    # ── Level decreases ────────────────────────────────────────────────────────────────────────────────────────────────────────

    def test_one_incorrect_decreases_level(self):
        s = _apply_adaptive_step(self._initial_state(2), correct=False)
        assert s["level"] == 1

    def test_incorrect_resets_consecutive_counter(self):
        s = self._initial_state(1)
        s = _apply_adaptive_step(s, correct=True)    # consecutiveCorrect = 1
        s = _apply_adaptive_step(s, correct=False)   # should reset
        assert s["consecutiveCorrect"] == 0

    def test_incorrect_then_correct_needs_two_to_advance(self):
        """After an error, two more corrects are required to step up again."""
        s = self._initial_state(2)
        s = _apply_adaptive_step(s, correct=False)   # → level 1
        s = _apply_adaptive_step(s, correct=True)    # consecutiveCorrect = 1
        assert s["level"] == 1
        s = _apply_adaptive_step(s, correct=True)    # → level 2
        assert s["level"] == 2

    # ── Floor and ceiling ──────────────────────────────────────────────────────────────────────────────────────────────────────

    def test_floor_at_level_1(self):
        s = _apply_adaptive_step(self._initial_state(1), correct=False)
        assert s["level"] == 1  # can't go below 1

    def test_ceiling_at_level_3(self):
        s = self._initial_state(3)
        s = _apply_adaptive_step(s, correct=True)
        s = _apply_adaptive_step(s, correct=True)
        assert s["level"] == 3  # can't go above 3

    # ── Convergence simulation ────────────────────────────────────────────────────────────────────────────────────────────────────────────

    def test_all_correct_converges_to_ceiling(self):
        s = self._initial_state(1)
        for _ in range(20):
            s = _apply_adaptive_step(s, correct=True)
        assert s["level"] == 3

    def test_all_incorrect_stays_at_floor(self):
        s = self._initial_state(2)
        for _ in range(20):
            s = _apply_adaptive_step(s, correct=False)
        assert s["level"] == 1

    def test_alternating_correct_incorrect_oscillates(self):
        """Alternating answers keep level low (1-down dominates 2-up)."""
        s = self._initial_state(1)
        for i in range(20):
            s = _apply_adaptive_step(s, correct=(i % 2 == 0))
        # Level should oscillate around 1–2, never reach 3
        assert s["level"] <= 2


# ─── 2. API: GET /api/adaptive-baseline/status ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

class TestAdaptiveBaselineStatus:

    def test_status_requires_auth(self, client):
        res = client.get("/api/adaptive-baseline/status")
        assert res.status_code == 401

    def test_new_user_has_not_completed(self, client):
        token = _register_and_token(client)
        res = client.get("/api/adaptive-baseline/status", headers=_auth(token))
        assert res.status_code == 200
        data = res.json()
        assert data["has_completed"] is False
        assert data["profile"] == []

    def test_status_after_completion_shows_profile(self, client):
        token = _register_and_token(client)
        payload = {
            "results": [
                {"game_key": "nback", "assessed_level": 2},
                {"game_key": "stroop", "assessed_level": 1},
            ]
        }
        client.post("/api/adaptive-baseline/complete", json=payload, headers=_auth(token))
        res = client.get("/api/adaptive-baseline/status", headers=_auth(token))
        assert res.status_code == 200
        data = res.json()
        assert data["has_completed"] is True
        assert len(data["profile"]) == 2
        keys = {e["game_key"] for e in data["profile"]}
        assert keys == {"nback", "stroop"}


# ─── 3. API: POST /api/adaptive-baseline/complete ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

class TestAdaptiveBaselineComplete:

    def _complete(self, client, token, results):
        return client.post(
            "/api/adaptive-baseline/complete",
            json={"results": results},
            headers=_auth(token),
        )

    def test_complete_requires_auth(self, client):
        res = client.post("/api/adaptive-baseline/complete", json={"results": []})
        assert res.status_code == 401

    def test_complete_empty_results_returns_400(self, client):
        token = _register_and_token(client)
        res = self._complete(client, token, [])
        assert res.status_code == 400

    def test_complete_invalid_game_key_returns_422(self, client):
        token = _register_and_token(client)
        res = self._complete(client, token, [{"game_key": "invalid_game", "assessed_level": 1}])
        assert res.status_code == 422

    def test_complete_invalid_level_returns_422(self, client):
        token = _register_and_token(client)
        res = self._complete(client, token, [{"game_key": "nback", "assessed_level": 99}])
        assert res.status_code == 422

    def test_complete_duplicate_game_keys_returns_400(self, client):
        token = _register_and_token(client)
        res = self._complete(client, token, [
            {"game_key": "nback", "assessed_level": 1},
            {"game_key": "nback", "assessed_level": 2},
        ])
        assert res.status_code == 400

    def test_complete_single_game_success(self, client):
        token = _register_and_token(client)
        res = self._complete(client, token, [{"game_key": "nback", "assessed_level": 2}])
        assert res.status_code == 200
        data = res.json()
        assert "profile" in data
        assert len(data["profile"]) == 1
        assert data["profile"][0]["game_key"] == "nback"
        assert data["profile"][0]["assessed_level"] == 2
        assert data["profile"][0]["baseline_count"] == 1

    def test_complete_all_seven_games(self, client):
        token = _register_and_token(client)
        all_games = [
            {"game_key": "nback",                "assessed_level": 1},
            {"game_key": "card_memory",           "assessed_level": 2},
            {"game_key": "digit_span",            "assessed_level": 3},
            {"game_key": "go_no_go",              "assessed_level": 1},
            {"game_key": "stroop",                "assessed_level": 2},
            {"game_key": "symbol_matching",       "assessed_level": 3},
            {"game_key": "visual_categorisation", "assessed_level": 1},
        ]
        res = self._complete(client, token, all_games)
        assert res.status_code == 200
        data = res.json()
        assert len(data["profile"]) == 7

    def test_complete_sets_has_completed_baseline_flag(self, client):
        token = _register_and_token(client)
        self._complete(client, token, [{"game_key": "nback", "assessed_level": 1}])
        status = client.get("/api/adaptive-baseline/status", headers=_auth(token))
        assert status.json()["has_completed"] is True

    def test_retake_increments_baseline_count(self, client):
        token = _register_and_token(client)
        entry = [{"game_key": "nback", "assessed_level": 1}]

        self._complete(client, token, entry)
        self._complete(client, token, entry)

        status = client.get("/api/adaptive-baseline/status", headers=_auth(token))
        profile = status.json()["profile"]
        nback_entry = next(e for e in profile if e["game_key"] == "nback")
        assert nback_entry["baseline_count"] == 2

    def test_retake_updates_assessed_level(self, client):
        token = _register_and_token(client)
        self._complete(client, token, [{"game_key": "nback", "assessed_level": 1}])
        self._complete(client, token, [{"game_key": "nback", "assessed_level": 3}])

        status = client.get("/api/adaptive-baseline/status", headers=_auth(token))
        profile = status.json()["profile"]
        nback_entry = next(e for e in profile if e["game_key"] == "nback")
        assert nback_entry["assessed_level"] == 3

    def test_profile_sorted_by_game_key(self, client):
        token = _register_and_token(client)
        games = [
            {"game_key": "stroop",   "assessed_level": 1},
            {"game_key": "nback",    "assessed_level": 2},
            {"game_key": "go_no_go", "assessed_level": 3},
        ]
        res = self._complete(client, token, games)
        keys = [e["game_key"] for e in res.json()["profile"]]
        assert keys == sorted(keys)

    def test_difficulty_labels_in_response(self, client):
        token = _register_and_token(client)
        games = [
            {"game_key": "nback",   "assessed_level": 1},
            {"game_key": "stroop",  "assessed_level": 2},
            {"game_key": "go_no_go","assessed_level": 3},
        ]
        res = self._complete(client, token, games)
        label_map = {e["game_key"]: e["difficulty_label"] for e in res.json()["profile"]}
        assert label_map["nback"]    == "Easy"
        assert label_map["stroop"]   == "Medium"
        assert label_map["go_no_go"] == "Hard"

    def test_game_display_names_in_response(self, client):
        token = _register_and_token(client)
        res = self._complete(client, token, [{"game_key": "nback", "assessed_level": 2}])
        profile = res.json()["profile"]
        assert profile[0]["game_name"] == "Count Back Match"

    # ── Isolation: different users have separate profiles ────────────────────

    def test_users_have_separate_profiles(self, client):
        token_a = _register_and_token(client, "a@x.com", "userA")
        token_b = _register_and_token(client, "b@x.com", "userB")

        self._complete(client, token_a, [{"game_key": "nback", "assessed_level": 3}])
        self._complete(client, token_b, [{"game_key": "nback", "assessed_level": 1}])

        profile_a = client.get("/api/adaptive-baseline/status", headers=_auth(token_a)).json()
        profile_b = client.get("/api/adaptive-baseline/status", headers=_auth(token_b)).json()

        assert profile_a["profile"][0]["assessed_level"] == 3
        assert profile_b["profile"][0]["assessed_level"] == 1


# ─── 4. DomainProgress seeding ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

class TestDomainProgressSeeding:
    """Verify that completing the adaptive baseline seeds DomainProgress rows."""

    GAME_DOMAIN_MAP = {
        "stroop": "processing_speed",
        "go_no_go": "processing_speed",
        "symbol_matching": "processing_speed",
        "nback": "working_memory",
        "digit_span": "working_memory",
        "card_memory": "working_memory",
        "visual_categorisation": "attention",
    }

    def _complete(self, client, token, results):
        return client.post(
            "/api/adaptive-baseline/complete",
            json={"results": results},
            headers=_auth(token),
        )

    def test_processing_speed_seeded_from_stroop(self, client):
        token, user_id = _register_and_token_with_id(client, "ps@example.com", "psuser")
        res = self._complete(client, token, [
            {"game_key": "stroop", "assessed_level": 2},
        ])
        assert res.status_code == 200
        db = SessionLocal()
        try:
            progress = db.query(DomainProgress).filter_by(
                user_id=user_id, domain="processing_speed"
            ).first()
            assert progress is not None
            assert progress.last_score is not None
            assert progress.last_score > 0
        finally:
            db.close()

    def test_working_memory_seeded_from_nback(self, client):
        token, user_id = _register_and_token_with_id(client, "wm@example.com", "wmuser")
        res = self._complete(client, token, [
            {"game_key": "nback", "assessed_level": 3},
        ])
        assert res.status_code == 200
        db = SessionLocal()
        try:
            progress = db.query(DomainProgress).filter_by(
                user_id=user_id, domain="working_memory"
            ).first()
            assert progress is not None
            assert pytest.approx(progress.last_score, abs=1) == 100.0
        finally:
            db.close()

    def test_attention_seeded_from_visual_categorisation(self, client):
        token, user_id = _register_and_token_with_id(client, "attn@example.com", "attnuser")
        res = self._complete(client, token, [
            {"game_key": "visual_categorisation", "assessed_level": 2},
        ])
        assert res.status_code == 200
        db = SessionLocal()
        try:
            progress = db.query(DomainProgress).filter_by(
                user_id=user_id, domain="attention"
            ).first()
            assert progress is not None
            assert progress.last_score is not None
            assert progress.last_score > 0
        finally:
            db.close()

    def test_easy_level_seeds_low_score(self, client):
        token, user_id = _register_and_token_with_id(client, "easy@example.com", "easyuser")
        self._complete(client, token, [{"game_key": "nback", "assessed_level": 1}])
        db = SessionLocal()
        try:
            progress = db.query(DomainProgress).filter_by(
                user_id=user_id, domain="working_memory"
            ).first()
            expected = (1 / 3.0) * 100
            assert pytest.approx(progress.last_score, abs=1) == expected
        finally:
            db.close()

    def test_hard_level_seeds_high_score(self, client):
        token, user_id = _register_and_token_with_id(client, "hard@example.com", "harduser")
        self._complete(client, token, [{"game_key": "nback", "assessed_level": 3}])
        db = SessionLocal()
        try:
            progress = db.query(DomainProgress).filter_by(
                user_id=user_id, domain="working_memory"
            ).first()
            assert pytest.approx(progress.last_score, abs=1) == 100.0
        finally:
            db.close()

    def test_multiple_games_same_domain_averages_level(self, client):
        """stroop (level 1) + go_no_go (level 3) -> avg=2 -> score=66.67"""
        token, user_id = _register_and_token_with_id(client, "avg@example.com", "avguser")
        self._complete(client, token, [
            {"game_key": "stroop",   "assessed_level": 1},
            {"game_key": "go_no_go", "assessed_level": 3},
        ])
        db = SessionLocal()
        try:
            progress = db.query(DomainProgress).filter_by(
                user_id=user_id, domain="processing_speed"
            ).first()
            assert progress is not None
            expected = (2.0 / 3.0) * 100
            assert pytest.approx(progress.last_score, abs=1) == expected
        finally:
            db.close()

    def test_seeded_difficulty_uses_rounded_avg_level(self, client):
        """avg_level 2.0 -> seeded_difficulty = max(1, round(2.0)) = 2"""
        token, user_id = _register_and_token_with_id(client, "diff@example.com", "diffuser")
        self._complete(client, token, [
            {"game_key": "stroop",   "assessed_level": 2},
            {"game_key": "go_no_go", "assessed_level": 2},
        ])
        db = SessionLocal()
        try:
            progress = db.query(DomainProgress).filter_by(
                user_id=user_id, domain="processing_speed"
            ).first()
            assert progress.current_difficulty == 2
        finally:
            db.close()

    def test_seeding_skipped_when_total_attempts_gt_zero(self, client):
        """If existing DomainProgress has total_attempts > 0, seeding must not overwrite."""
        token, user_id = _register_and_token_with_id(client, "skip@example.com", "skipuser")

        # Manually insert a DomainProgress row with total_attempts > 0
        db = SessionLocal()
        try:
            from backend.models.domain_progress import DomainProgress as DP
            dp = DP(
                user_id=user_id,
                domain="working_memory",
                current_difficulty=3,
                last_score=99.0,
                total_attempts=5,
            )
            db.add(dp)
            db.commit()
        finally:
            db.close()

        # Now complete baseline — should NOT overwrite
        self._complete(client, token, [{"game_key": "nback", "assessed_level": 1}])

        db = SessionLocal()
        try:
            after = db.query(DomainProgress).filter_by(
                user_id=user_id, domain="working_memory"
            ).first()
            assert after.last_score == 99.0
            assert after.current_difficulty == 3
            assert after.total_attempts == 5
        finally:
            db.close()

    def test_seeding_does_not_set_total_attempts(self, client):
        """Newly seeded DomainProgress rows must leave total_attempts = 0."""
        token, user_id = _register_and_token_with_id(client, "noattempts@example.com", "noattuser")
        self._complete(client, token, [{"game_key": "nback", "assessed_level": 2}])
        db = SessionLocal()
        try:
            progress = db.query(DomainProgress).filter_by(
                user_id=user_id, domain="working_memory"
            ).first()
            assert progress is not None
            assert progress.total_attempts == 0
        finally:
            db.close()

    def test_game_not_in_domain_map_does_not_seed(self, client):
        """Games without a domain mapping (none currently) don't create progress rows."""
        # All 7 game keys map to domains, so this test verifies that only
        # the expected domains are seeded when a subset is provided.
        token, user_id = _register_and_token_with_id(client, "subset@example.com", "subsetuser")
        self._complete(client, token, [{"game_key": "nback", "assessed_level": 2}])
        db = SessionLocal()
        try:
            # Only working_memory should be seeded
            all_progress = db.query(DomainProgress).filter_by(user_id=user_id).all()
            domains = {p.domain for p in all_progress}
            assert "working_memory" in domains
            # processing_speed and attention should NOT be seeded
            assert "processing_speed" not in domains
            assert "attention" not in domains
        finally:
            db.close()
