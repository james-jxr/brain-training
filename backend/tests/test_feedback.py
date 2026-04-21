"""
Regression tests: feedback submission and export.
"""
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


def _register_and_token(client, email="feedback@example.com"):
    res = client.post("/api/auth/register", json={
        "email": email,
        "username": email.split("@")[0],
        "password": "TestPass123!",
        "consent_given": True,
    })
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


class TestFeedbackSubmission:

    def test_submit_feedback_success(self, client):
        token = _register_and_token(client)
        res = client.post("/api/feedback", json={
            "page_context": "dashboard",
            "feedback_text": "Love the new design!",
        }, headers=_auth(token))
        assert res.status_code == 200

    def test_submit_feedback_unauthenticated_allowed(self, client):
        """Anonymous feedback is accepted (user_id nullable)."""
        res = client.post("/api/feedback", json={
            "page_context": "landing",
            "feedback_text": "Looks interesting.",
        })
        assert res.status_code == 200

    def test_submit_feedback_with_session_id(self, client):
        token = _register_and_token(client)
        sess = client.post("/api/sessions/start", json={
            "domain_1": "working_memory",
            "domain_2": "attention",
            "is_baseline": 0,
        }, headers=_auth(token))
        session_id = sess.json()["id"]

        res = client.post("/api/feedback", json={
            "page_context": "session_summary",
            "feedback_text": "Great session!",
            "session_id": session_id,
        }, headers=_auth(token))
        assert res.status_code == 200

    def test_submit_feedback_empty_text_rejected(self, client):
        token = _register_and_token(client)
        res = client.post("/api/feedback", json={
            "page_context": "dashboard",
            "feedback_text": "",
        }, headers=_auth(token))
        assert res.status_code in (400, 422)

    def test_submit_feedback_missing_page_context_rejected(self, client):
        token = _register_and_token(client)
        res = client.post("/api/feedback", json={
            "feedback_text": "Some feedback",
        }, headers=_auth(token))
        assert res.status_code == 422


class TestFeedbackExport:

    @pytest.fixture(autouse=True)
    def set_admin_env(self, monkeypatch):
        monkeypatch.setenv("ADMIN_EMAILS", "feedback@example.com")

    def test_export_feedback_authenticated(self, client):
        token = _register_and_token(client)
        client.post("/api/feedback", json={
            "page_context": "dashboard",
            "feedback_text": "Test feedback",
        }, headers=_auth(token))
        res = client.get("/api/feedback", headers=_auth(token))
        assert res.status_code == 200

    def test_export_contains_submitted_feedback(self, client):
        token = _register_and_token(client)
        client.post("/api/feedback", json={
            "page_context": "progress",
            "feedback_text": "Graphs are helpful",
        }, headers=_auth(token))
        res = client.get("/api/feedback", headers=_auth(token))
        data = res.json()
        all_entries = [e for g in data["groups"] for e in g["entries"]]
        texts = [e["feedback_text"] for e in all_entries]
        assert "Graphs are helpful" in texts

    def test_multiple_feedback_entries_all_returned(self, client):
        token = _register_and_token(client)
        for i in range(3):
            client.post("/api/feedback", json={
                "page_context": "session",
                "feedback_text": f"Feedback {i}",
            }, headers=_auth(token))
        res = client.get("/api/feedback", headers=_auth(token))
        assert res.json()["total"] >= 3

    def test_export_unauthenticated_rejected(self, client):
        res = client.get("/api/feedback")
        assert res.status_code == 401
