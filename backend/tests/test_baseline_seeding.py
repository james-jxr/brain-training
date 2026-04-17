"""
Regression tests: completing the adaptive baseline seeds DomainProgress
so that BrainHealthScore is non-zero on first login.
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine
from backend.models.domain_progress import DomainProgress
from backend.database import SessionLocal


@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    with TestClient(app) as c:
        yield c


def _register_and_token(client, email="seed@example.com"):
    res = client.post("/api/auth/register", json={
        "email": email,
        "username": email.split("@")[0],
        "password": "TestPass123!",
        "consent_given": True,
    })
    assert res.status_code == 200, res.text
    return res.json()["access_token"], res.json()["user"]["id"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _complete_baseline(client, token, results):
    return client.post(
        "/api/adaptive-baseline/complete",
        json={"results": results},
        headers=_auth(token),
    )


# ─── DomainProgress seeding ───────────────────────────────────────────────────

class TestBaselineSeeding:

    def test_processing_speed_seeded_from_stroop_and_go_no_go(self, client):
        token, user_id = _register_and_token(client)
        _complete_baseline(client, token, [
            {"game_key": "stroop",   "assessed_level": 2},
            {"game_key": "go_no_go", "assessed_level": 2},
        ])
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

    def test_working_memory_seeded_from_nback_and_digit_span(self, client):
        token, user_id = _register_and_token(client)
        _complete_baseline(client, token, [
            {"game_key": "nback",      "assessed_level": 3},
            {"game_key": "digit_span", "assessed_level": 3},
        ])
        db = SessionLocal()
        try:
            progress = db.query(DomainProgress).filter_by(
                user_id=user_id, domain="working_memory"
            ).first()
            assert progress is not None
            assert pytest.approx(progress.last_score, abs=1) == 100.0
        finally:
            db.close()

    def test_attention_seeded_from_go_no_go_and_stroop(self, client):
        token, user_id = _register_and_token(client)
        _complete_baseline(client, token, [
            {"game_key": "go_no_go", "assessed_level": 1},
            {"game_key": "stroop",   "assessed_level": 1},
        ])
        db = SessionLocal()
        try:
            progress = db.query(DomainProgress).filter_by(
                user_id=user_id, domain="processing_speed"
            ).first()
            assert progress is not None
            # assessed_level 1 → score ~33%
            assert progress.last_score < 50
        finally:
            db.close()

    def test_easy_level_seeds_low_score(self, client):
        token, user_id = _register_and_token(client)
        _complete_baseline(client, token, [
            {"game_key": "nback", "assessed_level": 1},
        ])
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
        token, user_id = _register_and_token(client)
        _complete_baseline(client, token, [
            {"game_key": "nback", "assessed_level": 3},
        ])
        db = SessionLocal()
        try:
            progress = db.query(DomainProgress).filter_by(
                user_id=user_id, domain="working_memory"
            ).first()
            assert pytest.approx(progress.last_score, abs=1) == 100.0
        finally:
            db.close()

    def test_seeding_does_not_overwrite_existing_training_data(self, client):
        token, user_id = _register_and_token(client)

        # First, do a training session that builds real DomainProgress
        sess = client.post("/api/sessions/start", json={
            "domain_1": "working_memory",
            "domain_2": "working_memory",
            "is_baseline": 0,
        }, headers=_auth(token))
        session_id = sess.json()["id"]
        client.post(f"/api/sessions/{session_id}/exercise-result", json={
            "domain": "working_memory",
            "exercise_type": "n_back",
            "trials_presented": 10,
            "trials_correct": 9,
            "avg_response_ms": 400.0,
        }, headers=_auth(token))

        db = SessionLocal()
        try:
            before = db.query(DomainProgress).filter_by(
                user_id=user_id, domain="working_memory"
            ).first()
            score_before = before.total_attempts if before else 0
        finally:
            db.close()

        # Now complete baseline — should NOT overwrite since total_attempts > 0
        _complete_baseline(client, token, [
            {"game_key": "nback", "assessed_level": 1},
        ])

        db = SessionLocal()
        try:
            after = db.query(DomainProgress).filter_by(
                user_id=user_id, domain="working_memory"
            ).first()
            # total_attempts should be unchanged (seeding skipped)
            assert after.total_attempts == score_before
        finally:
            db.close()


# ─── BrainHealthScore non-zero after baseline ─────────────────────────────────

class TestBrainHealthAfterBaseline:

    def test_brain_health_score_non_zero_after_baseline(self, client):
        token, _ = _register_and_token(client)
        _complete_baseline(client, token, [
            {"game_key": "nback",      "assessed_level": 2},
            {"game_key": "digit_span", "assessed_level": 2},
            {"game_key": "stroop",     "assessed_level": 2},
            {"game_key": "go_no_go",   "assessed_level": 2},
        ])
        res = client.get("/api/progress/brain-health", headers=_auth(token))
        assert res.status_code == 200
        assert res.json()["brain_health_score"] > 0

    def test_brain_health_score_zero_before_baseline(self, client):
        token, _ = _register_and_token(client)
        res = client.get("/api/progress/brain-health", headers=_auth(token))
        assert res.status_code == 200
        assert res.json()["brain_health_score"] == 0
