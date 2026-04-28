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


def _register_and_token(client, email="baseline@example.com", username="baselineuser"):
    res = client.post("/api/auth/register", json={
        "email": email,
        "username": username,
        "password": "TestPass123!",
        "consent_given": True,
    })
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


class TestBaselineSubmit:

    def test_submit_sets_has_completed_baseline(self, client):
        token = _register_and_token(client)
        res = client.post(
            "/api/baseline/submit",
            json=[
                {"domain": "processing_speed", "score": 75.0},
                {"domain": "working_memory", "score": 80.0},
            ],
            headers=_auth(token),
        )
        assert res.status_code == 200, res.text

        me = client.get("/api/auth/me", headers=_auth(token))
        assert me.status_code == 200
        assert me.json()["has_completed_baseline"] is True
