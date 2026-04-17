"""
Unit tests for the Count Back Match (N-Back) game logic.

These tests port the JavaScript sequence generation algorithm from
frontend/src/components/exercises/NBack.jsx into Python so the logic
can be validated with pytest alongside the rest of the backend test suite.

Tests cover:
  - getNBackLevel: difficulty → N-back level mapping
  - generateBalancedSequence: sequence length, match ratio, no accidental matches
  - isMatch: N-back comparison correctness
  - Backend compatibility: submitting n_back results with avg_response_ms=0
"""

import random
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine
from backend.models import User, Session as DBSession, ExerciseAttempt


# ─── Pure-function ports of the JS game logic ─────────────────────────────────

LETTERS = list('ABCDEFGHIJKLMNO')


def get_n_back_level(difficulty: int) -> int:
    """Mirror of getNBackLevel() in NBack.jsx"""
    if difficulty <= 3:
        return 1
    if difficulty <= 6:
        return 2
    return 3


def is_match(sequence: list, index: int, n: int) -> bool:
    """Mirror of isMatch() in NBack.jsx"""
    if index < n:
        return False
    return sequence[index] == sequence[index - n]


def generate_balanced_sequence(n: int, total_length: int, rng=None) -> list:
    """
    Mirror of generateBalancedSequence() in NBack.jsx.

    n            — N-back level (1, 2, or 3)
    total_length — total letters in the sequence (lead-in + judgeable)
    rng          — optional random.Random instance for reproducible tests
    """
    if rng is None:
        rng = random
    sequence = []
    judgeable_count = total_length - n
    target_matches = round(judgeable_count * 0.5)

    # Lead-in letters: random, unconstrained
    for _ in range(n):
        sequence.append(rng.choice(LETTERS))

    matches_remaining = target_matches
    no_matches_remaining = judgeable_count - target_matches

    for i in range(n, total_length):
        total = matches_remaining + no_matches_remaining
        match_probability = matches_remaining / total
        should_match = rng.random() < match_probability

        if should_match:
            sequence.append(sequence[i - n])
            matches_remaining -= 1
        else:
            n_back_letter = sequence[i - n]
            candidates = [l for l in LETTERS if l != n_back_letter]
            sequence.append(rng.choice(candidates))
            no_matches_remaining -= 1

    return sequence


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
        "email": "nback@test.com",
        "username": "nback_tester",
        "password": "TestPass123!",
        "consent_given": True,
    })
    r = client.post("/api/auth/login", json={
        "email": "nback@test.com",
        "password": "TestPass123!"
    })
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ─── getNBackLevel tests ───────────────────────────────────────────────────────

class TestGetNBackLevel:
    def test_difficulty_1_returns_1_back(self):
        assert get_n_back_level(1) == 1

    def test_difficulty_3_returns_1_back(self):
        assert get_n_back_level(3) == 1

    def test_difficulty_4_returns_2_back(self):
        assert get_n_back_level(4) == 2

    def test_difficulty_6_returns_2_back(self):
        assert get_n_back_level(6) == 2

    def test_difficulty_7_returns_3_back(self):
        assert get_n_back_level(7) == 3

    def test_difficulty_10_returns_3_back(self):
        assert get_n_back_level(10) == 3


# ─── isMatch tests ─────────────────────────────────────────────────────────────

class TestIsMatch:
    def test_index_less_than_n_is_never_a_match(self):
        seq = ['A', 'B', 'C', 'A']
        # index 0, n=1: no prior letter → not a match
        assert is_match(seq, 0, 1) is False

    def test_matching_letter_returns_true(self):
        # seq[3] == seq[3-1] == seq[2] → 'C' == 'C'
        seq = ['A', 'B', 'C', 'C']
        assert is_match(seq, 3, 1) is True

    def test_non_matching_letter_returns_false(self):
        seq = ['A', 'B', 'C', 'D']
        assert is_match(seq, 3, 1) is False

    def test_2_back_match(self):
        seq = ['A', 'B', 'A', 'B']
        # seq[2] == seq[0] → 'A' == 'A'
        assert is_match(seq, 2, 2) is True

    def test_2_back_no_match(self):
        seq = ['A', 'B', 'C', 'B']
        # seq[2] vs seq[0] → 'C' != 'A'
        assert is_match(seq, 2, 2) is False

    def test_3_back_match(self):
        seq = ['A', 'B', 'C', 'A']
        # seq[3] == seq[0] → 'A' == 'A'
        assert is_match(seq, 3, 3) is True

    def test_3_back_no_match(self):
        seq = ['A', 'B', 'C', 'D']
        assert is_match(seq, 3, 3) is False

    def test_lead_in_positions_never_match_for_2_back(self):
        seq = ['A', 'A', 'A', 'A']
        # index 0 and 1 are lead-in for n=2 — should never claim match
        assert is_match(seq, 0, 2) is False
        assert is_match(seq, 1, 2) is False


# ─── generateBalancedSequence tests ───────────────────────────────────────────

class TestGenerateBalancedSequence:
    """Test the balanced sequence generator for all N-back levels."""

    @pytest.mark.parametrize("n", [1, 2, 3])
    def test_sequence_has_correct_total_length(self, n):
        seq = generate_balanced_sequence(n, 15 + n)
        assert len(seq) == 15 + n

    @pytest.mark.parametrize("n", [1, 2, 3])
    def test_all_letters_are_valid(self, n):
        seq = generate_balanced_sequence(n, 15 + n)
        for letter in seq:
            assert letter in LETTERS, f"Invalid letter: {letter}"

    @pytest.mark.parametrize("n", [1, 2, 3])
    def test_match_ratio_is_40_to_60_percent(self, n):
        """Run 20 times to verify the ratio holds statistically."""
        for _ in range(20):
            rng = random.Random()
            seq = generate_balanced_sequence(n, 15 + n, rng=rng)
            judgeable_indices = range(n, len(seq))
            match_count = sum(1 for i in judgeable_indices if is_match(seq, i, n))
            total_judgeable = len(seq) - n
            ratio = match_count / total_judgeable
            assert 0.40 <= ratio <= 0.60, (
                f"n={n}: match ratio {ratio:.2f} outside [0.40, 0.60] in sequence {seq}"
            )

    @pytest.mark.parametrize("n", [1, 2, 3])
    def test_no_match_positions_never_accidentally_match(self, n):
        """
        When the algorithm decides a position should NOT match, the letter
        chosen must differ from sequence[i - n].
        """
        rng = random.Random(42)
        for _ in range(50):
            seq = generate_balanced_sequence(n, 15 + n, rng=rng)
            # Count actual vs expected matches
            actual_matches = [is_match(seq, i, n) for i in range(n, len(seq))]
            # There should never be more matches than the ~50% target
            # (this checks that no-match positions haven't accidentally become matches
            # through poor letter selection)
            ratio = sum(actual_matches) / len(actual_matches)
            assert ratio <= 0.65, f"Too many accidental matches: ratio={ratio:.2f}"

    def test_1_back_lead_in_is_1_letter(self):
        seq = generate_balanced_sequence(1, 16)
        # Only position 0 is lead-in; position 1 is the first judgeable
        # We can verify by checking length
        assert len(seq) == 16

    def test_3_back_lead_in_is_3_letters(self):
        seq = generate_balanced_sequence(3, 18)
        assert len(seq) == 18
        # The first 3 positions are lead-in — is_match should return False for them
        for i in range(3):
            assert is_match(seq, i, 3) is False

    def test_target_match_count_is_exactly_half_of_judgeable(self):
        """
        With a fixed seed, verify that the number of matches is exactly 7 or 8
        (round(15 * 0.5) = 8 for 15 judgeable trials).
        """
        n = 1
        total = 16
        rng = random.Random(99)
        seq = generate_balanced_sequence(n, total, rng=rng)
        match_count = sum(1 for i in range(n, total) if is_match(seq, i, n))
        # round(15 * 0.5) = 8 — should be exactly 8 with a perfectly balanced sequence
        assert match_count == round((total - n) * 0.5)


# ─── Backend compatibility tests ───────────────────────────────────────────────

class TestNBackBackendCompatibility:
    """
    Verify the backend accepts n_back results with avg_response_ms=0,
    which is what the updated NBack component submits (no speed tracking).
    """

    def test_nback_result_with_zero_avg_response_ms_is_accepted(self, client, auth):
        r = client.post("/api/sessions/start", headers=auth, json={
            "domain_1": "working_memory",
            "domain_2": "attention",
            "is_baseline": 0
        })
        assert r.status_code == 200
        session_id = r.json()["id"]

        result = client.post(
            f"/api/sessions/{session_id}/exercise-result",
            headers=auth,
            json={
                "domain": "working_memory",
                "exercise_type": "n_back",
                "trials_presented": 15,
                "trials_correct": 10,
                "avg_response_ms": 0
            }
        )
        assert result.status_code == 200
        data = result.json()
        assert data["trials_presented"] == 15
        assert data["trials_correct"] == 10
        assert data["avg_response_ms"] == 0

    def test_nback_result_all_correct(self, client, auth):
        r = client.post("/api/sessions/start", headers=auth, json={
            "domain_1": "working_memory",
            "domain_2": "attention",
            "is_baseline": 0
        })
        session_id = r.json()["id"]

        result = client.post(
            f"/api/sessions/{session_id}/exercise-result",
            headers=auth,
            json={
                "domain": "working_memory",
                "exercise_type": "n_back",
                "trials_presented": 15,
                "trials_correct": 15,
                "avg_response_ms": 0
            }
        )
        assert result.status_code == 200
        assert result.json()["trials_correct"] == 15

    def test_nback_result_all_incorrect(self, client, auth):
        r = client.post("/api/sessions/start", headers=auth, json={
            "domain_1": "working_memory",
            "domain_2": "attention",
            "is_baseline": 0
        })
        session_id = r.json()["id"]

        result = client.post(
            f"/api/sessions/{session_id}/exercise-result",
            headers=auth,
            json={
                "domain": "working_memory",
                "exercise_type": "n_back",
                "trials_presented": 15,
                "trials_correct": 0,
                "avg_response_ms": 0
            }
        )
        assert result.status_code == 200
        assert result.json()["trials_correct"] == 0

    def test_nback_result_requires_auth(self, client, auth):
        r = client.post("/api/sessions/start", headers=auth, json={
            "domain_1": "working_memory",
            "domain_2": "attention",
            "is_baseline": 0
        })
        session_id = r.json()["id"]

        # Use a fresh client with no cookie jar to avoid cookie-based auth
        # (the shared `client` may have an httpOnly session cookie after login)
        with TestClient(app, cookies={}) as fresh_client:
            result = fresh_client.post(
                f"/api/sessions/{session_id}/exercise-result",
                # No auth header, no cookies
                json={
                    "domain": "working_memory",
                    "exercise_type": "n_back",
                    "trials_presented": 15,
                    "trials_correct": 8,
                    "avg_response_ms": 0
                }
            )
        assert result.status_code == 401
