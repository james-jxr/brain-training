import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal, Base, engine

@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    with TestClient(app) as c:
        yield c

@pytest.fixture
def authenticated_client(client):
    """Returns (client, auth_headers) tuple. Pass auth_headers to each request."""
    client.post("/api/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123",
        "consent_given": True,
    })
    login_response = client.post("/api/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    token = login_response.json()["access_token"]
    return client, {"Authorization": f"Bearer {token}"}

def test_start_session(authenticated_client):
    client, auth = authenticated_client
    response = client.post("/api/sessions/start", json={
        "domain_1": "processing_speed",
        "domain_2": "working_memory",
        "is_baseline": 0
    }, headers=auth)
    assert response.status_code == 200
    assert response.json()["domain_1"] == "processing_speed"
    assert response.json()["domain_2"] == "working_memory"

def test_log_exercise_result(authenticated_client):
    client, auth = authenticated_client
    session_response = client.post("/api/sessions/start", json={
        "domain_1": "processing_speed",
        "domain_2": "working_memory",
        "is_baseline": 0
    }, headers=auth)
    session_id = session_response.json()["id"]

    response = client.post(
        f"/api/sessions/{session_id}/exercise-result",
        json={
            "domain": "processing_speed",
            "exercise_type": "symbol_matching",
            "trials_presented": 8,
            "trials_correct": 7,
            "avg_response_ms": 1200.5
        },
        headers=auth
    )
    assert response.status_code == 200
    assert response.json()["trials_correct"] == 7

def test_complete_session(authenticated_client):
    client, auth = authenticated_client
    session_response = client.post("/api/sessions/start", json={
        "domain_1": "processing_speed",
        "domain_2": "working_memory",
        "is_baseline": 0
    }, headers=auth)
    session_id = session_response.json()["id"]

    response = client.post(f"/api/sessions/{session_id}/complete", headers=auth)
    assert response.status_code == 200
    assert "Session completed" in response.json()["message"]

def test_get_session(authenticated_client):
    client, auth = authenticated_client
    session_response = client.post("/api/sessions/start", json={
        "domain_1": "processing_speed",
        "domain_2": "working_memory",
        "is_baseline": 0
    }, headers=auth)
    session_id = session_response.json()["id"]

    response = client.get(f"/api/sessions/{session_id}", headers=auth)
    assert response.status_code == 200
    assert response.json()["id"] == session_id

def test_list_sessions(authenticated_client):
    client, auth = authenticated_client
    client.post("/api/sessions/start", json={
        "domain_1": "processing_speed",
        "domain_2": "working_memory",
        "is_baseline": 0
    }, headers=auth)
    client.post("/api/sessions/start", json={
        "domain_1": "attention",
        "domain_2": "working_memory",
        "is_baseline": 0
    }, headers=auth)

    response = client.get("/api/sessions", headers=auth)
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_plan_next_session(authenticated_client):
    client, auth = authenticated_client
    response = client.post("/api/sessions/plan-next", headers=auth)
    assert response.status_code == 200
    assert "domain_1" in response.json()
    assert "domain_2" in response.json()
