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
    return client.post("/api/auth/register", json={
        "email": email,
        "username": username,
        "password": password,
        "consent_given": True,
    })


# ─── Registration ─────────────────────────────────────────────────────────────

def test_register_success(client):
    res = _register(client)
    assert res.status_code == 200
    assert res.json()["user"]["email"] == "test@example.com"
    assert res.json()["user"]["username"] == "testuser"


def test_register_returns_access_token(client):
    res = _register(client)
    assert "access_token" in res.json()
    assert res.json()["token_type"] == "bearer"


def test_register_without_consent_rejected(client):
    res = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123",
        "consent_given": False,
    })
    assert res.status_code == 400
    assert "terms" in res.json()["detail"]["message"].lower()


def test_register_duplicate_email(client):
    _register(client)
    res = _register(client, username="otheruser")
    assert res.status_code == 400
    assert "Email already registered" in res.json()["detail"]["message"]


def test_register_duplicate_username(client):
    _register(client)
    res = _register(client, email="other@example.com")
    assert res.status_code == 400
    assert "Username already taken" in res.json()["detail"]["message"]


# ─── Login ────────────────────────────────────────────────────────────────────

def test_login_success(client):
    _register(client)
    res = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123",
    })
    assert res.status_code == 200
    assert res.json()["user"]["email"] == "test@example.com"


def test_login_returns_access_token(client):
    _register(client)
    res = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123",
    })
    assert "access_token" in res.json()


def test_login_invalid_password(client):
    _register(client)
    res = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword",
    })
    assert res.status_code == 401
    assert "Invalid credentials" in res.json()["detail"]["message"]


def test_login_unknown_email(client):
    res = client.post("/api/auth/login", json={
        "email": "nobody@example.com",
        "password": "password123",
    })
    assert res.status_code == 401


# ─── /me ─────────────────────────────────────────────────────────────────────

def test_get_current_user(client):
    res = _register(client)
    token = res.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "test@example.com"


def test_get_current_user_unauthenticated(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


# ─── Logout ───────────────────────────────────────────────────────────────────

def test_logout(client):
    _register(client)
    res = client.post("/api/auth/logout")
    assert res.status_code == 200
    assert "Logged out successfully" in res.json()["message"]
