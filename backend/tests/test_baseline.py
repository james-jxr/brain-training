"""Tests for the baseline router (BUG-14 / BUG-12 fixes).

Covers:
  1. POST /api/baseline/start  — creates a session, enforces eligibility via User-level field
  2. POST /api/baseline/submit — stores BaselineResult rows, sets onboarding flags,
                                  sets next_baseline_eligible_date, baseline_number logic
  3. GET  /api/baseline/next-eligible-date — returns User-level field as source of truth
"""
import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine, SessionLocal
from backend.models import User


@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    with TestClient(app) as c:
        yield c


# ─── helpers ──────────────────────────────────────────────────────────────────

def _register(client, email="bl@example.com", username="bluser", password="password123"):
    res = client.post("/api/auth/register", json={
        "email": email,
        "username": username,
        "password": password,
        "consent_given": True,
    })
    assert res.status_code == 200, res.text
    data = res.json()
    return data["access_token"], data["user"]["id"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _start(client, token):
    return client.post("/api/baseline/start", headers=_auth(token))


def _submit(client, token, domain_scores=None):
    if domain_scores is None:
        domain_scores = [
            {"domain": "processing_speed", "score": 70.0},
            {"domain": "working_memory",   "score": 60.0},
        ]
    return client.post("/api/baseline/submit", json=domain_scores, headers=_auth(token))


# ─── POST /api/baseline/start ─────────────────────────────────────────────────

class TestBaselineStart:

    def test_start_requires_auth(self, client):
        res = client.post("/api/baseline/start")
        assert res.status_code == 401

    def test_start_creates_session(self, client):
        token, _ = _register(client)
        res = _start(client, token)
        assert res.status_code == 200
        data = res.json()
        assert data["is_baseline"] == 1
        assert data["domain_1"] == "processing_speed"
        assert data["domain_2"] == "working_memory"

    def test_start_baseline_number_increments(self, client):
        token, _ = _register(client)
        r1 = _start(client, token)
        assert r1.status_code == 200
        assert r1.json()["baseline_number"] == 1

        r2 = _start(client, token)
        assert r2.status_code == 200
        assert r2.json()["baseline_number"] == 2

    def test_start_blocked_when_not_yet_eligible(self, client):
        """If next_baseline_eligible_date is in the future the request must be rejected."""
        token, user_id = _register(client)

        # Directly set next_baseline_eligible_date to future
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            user.next_baseline_eligible_date = date.today() + timedelta(days=90)
            db.commit()
        finally:
            db.close()

        res = _start(client, token)
        assert res.status_code == 400
        assert "Next baseline eligible on" in res.json()["detail"]["message"]

    def test_start_allowed_when_eligible_date_is_today(self, client):
        token, user_id = _register(client)

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            user.next_baseline_eligible_date = date.today()
            db.commit()
        finally:
            db.close()

        res = _start(client, token)
        assert res.status_code == 200

    def test_start_allowed_when_eligible_date_is_null(self, client):
        token, _ = _register(client)
        # New user has no eligible date set
        res = _start(client, token)
        assert res.status_code == 200


# ─── POST /api/baseline/submit ────────────────────────────────────────────────

class TestBaselineSubmit:

    def test_submit_requires_auth(self, client):
        res = client.post("/api/baseline/submit", json=[])
        assert res.status_code == 401

    def test_submit_returns_expected_shape(self, client):
        token, _ = _register(client)
        res = _submit(client, token)
        assert res.status_code == 200
        data = res.json()
        assert data["message"] == "Baseline submitted successfully"
        assert data["baseline_number"] == 1
        assert data["is_original"] is True
        assert len(data["results"]) == 2

    def test_submit_first_baseline_is_original(self, client):
        token, _ = _register(client)
        res = _submit(client, token)
        assert res.json()["is_original"] is True

    def test_submit_second_baseline_not_original(self, client):
        token, _ = _register(client)
        _submit(client, token)
        res = _submit(client, token)
        assert res.json()["is_original"] is False
        assert res.json()["baseline_number"] == 2

    def test_submit_increments_baseline_number_correctly(self, client):
        token, _ = _register(client)
        r1 = _submit(client, token)
        assert r1.json()["baseline_number"] == 1
        r2 = _submit(client, token)
        assert r2.json()["baseline_number"] == 2
        r3 = _submit(client, token)
        assert r3.json()["baseline_number"] == 3

    def test_submit_sets_onboarding_completed(self, client):
        token, user_id = _register(client)
        _submit(client, token)
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            assert user.onboarding_completed is True
            assert user.has_completed_baseline is True
        finally:
            db.close()

    def test_submit_sets_next_baseline_eligible_date(self, client):
        token, user_id = _register(client)
        _submit(client, token)
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            expected = date.today() + timedelta(days=180)
            assert user.next_baseline_eligible_date == expected
        finally:
            db.close()

    def test_submit_invalid_domain_returns_400(self, client):
        token, _ = _register(client)
        res = _submit(client, token, domain_scores=[
            {"domain": "not_a_real_domain", "score": 50.0}
        ])
        assert res.status_code == 400
        assert "Invalid domain" in res.json()["detail"]["message"]

    def test_submit_valid_domains_accepted(self, client):
        token, _ = _register(client)
        res = _submit(client, token, domain_scores=[
            {"domain": "processing_speed", "score": 80.0},
            {"domain": "working_memory",   "score": 70.0},
            {"domain": "attention",         "score": 60.0},
        ])
        assert res.status_code == 200
        assert len(res.json()["results"]) == 3

    def test_submit_result_fields(self, client):
        token, _ = _register(client)
        res = _submit(client, token, domain_scores=[
            {"domain": "processing_speed", "score": 75.5},
        ])
        result = res.json()["results"][0]
        assert result["domain"] == "processing_speed"
        assert result["score"] == 75.5
        assert result["baseline_number"] == 1
        assert result["is_original"] is True

    def test_submit_seeds_domain_progress(self, client):
        from backend.models import DomainProgress
        token, user_id = _register(client)
        _submit(client, token, domain_scores=[
            {"domain": "processing_speed", "score": 80.0},
        ])
        db = SessionLocal()
        try:
            progress = db.query(DomainProgress).filter_by(
                user_id=user_id, domain="processing_speed"
            ).first()
            assert progress is not None
            assert progress.last_score == 80.0
        finally:
            db.close()

    def test_submit_updates_existing_domain_progress(self, client):
        from backend.models import DomainProgress
        token, user_id = _register(client)
        _submit(client, token, domain_scores=[
            {"domain": "processing_speed", "score": 60.0},
        ])
        _submit(client, token, domain_scores=[
            {"domain": "processing_speed", "score": 90.0},
        ])
        db = SessionLocal()
        try:
            progress = db.query(DomainProgress).filter_by(
                user_id=user_id, domain="processing_speed"
            ).first()
            assert progress.last_score == 90.0
        finally:
            db.close()

    def test_users_have_independent_baseline_numbers(self, client):
        token_a, _ = _register(client, "a@bl.com", "userA")
        token_b, _ = _register(client, "b@bl.com", "userB")

        _submit(client, token_a)
        _submit(client, token_a)

        res_b = _submit(client, token_b)
        assert res_b.json()["baseline_number"] == 1


# ─── GET /api/baseline/next-eligible-date ─────────────────────────────────────

class TestNextEligibleDate:

    def test_requires_auth(self, client):
        res = client.get("/api/baseline/next-eligible-date")
        assert res.status_code == 401

    def test_new_user_is_eligible(self, client):
        token, _ = _register(client)
        res = client.get("/api/baseline/next-eligible-date", headers=_auth(token))
        assert res.status_code == 200
        data = res.json()
        assert data["is_eligible"] is True

    def test_after_submit_not_eligible(self, client):
        token, _ = _register(client)
        _submit(client, token)
        res = client.get("/api/baseline/next-eligible-date", headers=_auth(token))
        assert res.status_code == 200
        data = res.json()
        assert data["is_eligible"] is False

    def test_after_submit_next_eligible_date_is_180_days_away(self, client):
        token, _ = _register(client)
        _submit(client, token)
        res = client.get("/api/baseline/next-eligible-date", headers=_auth(token))
        expected = (date.today() + timedelta(days=180)).isoformat()
        assert res.json()["next_eligible_date"] == expected

    def test_eligible_date_today_means_eligible(self, client):
        token, user_id = _register(client)
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            user.next_baseline_eligible_date = date.today()
            db.commit()
        finally:
            db.close()

        res = client.get("/api/baseline/next-eligible-date", headers=_auth(token))
        assert res.json()["is_eligible"] is True

    def test_eligible_date_past_means_eligible(self, client):
        token, user_id = _register(client)
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            user.next_baseline_eligible_date = date.today() - timedelta(days=1)
            db.commit()
        finally:
            db.close()

        res = client.get("/api/baseline/next-eligible-date", headers=_auth(token))
        assert res.json()["is_eligible"] is True
