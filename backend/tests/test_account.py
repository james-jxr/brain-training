import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine


@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    with TestClient(app) as c:
        yield c


def _register(client, email="test@example.com", username="testuser", password="password123"):
    res = client.post("/api/auth/register", json={
        "email": email,
        "username": username,
        "password": password,
        "consent_given": True,
    })
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# ─── GET /api/account/profile ─────────────────────────────────────────────────

class TestGetProfile:
    def test_get_profile_requires_auth(self, client):
        res = client.get("/api/account/profile")
        assert res.status_code == 401

    def test_get_profile_returns_user_data(self, client):
        token = _register(client)
        res = client.get("/api/account/profile", headers=_auth(token))
        assert res.status_code == 200
        data = res.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"


# ─── POST /api/account/onboarding-complete ────────────────────────────────────

class TestOnboardingComplete:
    def test_onboarding_complete_requires_auth(self, client):
        res = client.post("/api/account/onboarding-complete")
        assert res.status_code == 401

    def test_onboarding_complete_sets_flag(self, client):
        token = _register(client)
        res = client.post("/api/account/onboarding-complete", headers=_auth(token))
        assert res.status_code == 200
        data = res.json()
        assert data["message"] == "Onboarding completed"
        assert data["user"]["onboarding_completed"] is True

    def test_onboarding_complete_idempotent(self, client):
        token = _register(client)
        client.post("/api/account/onboarding-complete", headers=_auth(token))
        res = client.post("/api/account/onboarding-complete", headers=_auth(token))
        assert res.status_code == 200
        assert res.json()["user"]["onboarding_completed"] is True


# ─── GET /api/account/onboarding-status ──────────────────────────────────────

class TestOnboardingStatus:
    def test_onboarding_status_requires_auth(self, client):
        res = client.get("/api/account/onboarding-status")
        assert res.status_code == 401

    def test_onboarding_status_default_false(self, client):
        token = _register(client)
        res = client.get("/api/account/onboarding-status", headers=_auth(token))
        assert res.status_code == 200
        assert res.json()["onboarding_completed"] is False

    def test_onboarding_status_true_after_completion(self, client):
        token = _register(client)
        client.post("/api/account/onboarding-complete", headers=_auth(token))
        res = client.get("/api/account/onboarding-status", headers=_auth(token))
        assert res.status_code == 200
        assert res.json()["onboarding_completed"] is True


# ─── PATCH /api/account ───────────────────────────────────────────────────────

class TestUpdateAccount:
    def test_update_requires_auth(self, client):
        res = client.patch("/api/account", json={"email": "new@example.com"})
        assert res.status_code == 401

    def test_update_email(self, client):
        token = _register(client)
        res = client.patch("/api/account", json={"email": "new@example.com"}, headers=_auth(token))
        assert res.status_code == 200
        assert res.json()["email"] == "new@example.com"

    def test_update_email_duplicate_returns_400(self, client):
        token_a = _register(client, email="a@example.com", username="userA")
        _register(client, email="b@example.com", username="userB")
        res = client.patch("/api/account", json={"email": "b@example.com"}, headers=_auth(token_a))
        assert res.status_code == 400
        assert "Email already in use" in res.json()["detail"]["message"]

    def test_update_password(self, client):
        token = _register(client)
        res = client.patch("/api/account", json={"password": "newpassword123"}, headers=_auth(token))
        assert res.status_code == 200

    def test_update_password_too_short_returns_422(self, client):
        token = _register(client)
        res = client.patch("/api/account", json={"password": "short"}, headers=_auth(token))
        assert res.status_code == 422

    def test_update_notification_time(self, client):
        token = _register(client)
        res = client.patch("/api/account", json={"notification_time": "08:00"}, headers=_auth(token))
        assert res.status_code == 200

    def test_update_no_fields_is_ok(self, client):
        token = _register(client)
        res = client.patch("/api/account", json={}, headers=_auth(token))
        assert res.status_code == 200

    def test_same_email_does_not_conflict_with_self(self, client):
        token = _register(client, email="me@example.com")
        res = client.patch("/api/account", json={"email": "me@example.com"}, headers=_auth(token))
        assert res.status_code == 200


# ─── DELETE /api/account ──────────────────────────────────────────────────────

class TestDeleteAccount:
    def test_delete_requires_auth(self, client):
        res = client.delete("/api/account")
        assert res.status_code == 401

    def test_delete_account_success(self, client):
        token = _register(client)
        res = client.delete("/api/account", headers=_auth(token))
        assert res.status_code == 200
        assert res.json()["message"] == "Account deleted successfully"

    def test_deleted_user_cannot_login(self, client):
        token = _register(client)
        client.delete("/api/account", headers=_auth(token))
        res = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "password123",
        })
        assert res.status_code == 401

    def test_deleted_user_token_no_longer_valid(self, client):
        token = _register(client)
        client.delete("/api/account", headers=_auth(token))
        res = client.get("/api/account/profile", headers=_auth(token))
        assert res.status_code == 401
