import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine


@pytest.fixture(scope='function')
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    with TestClient(app) as c:
        yield c


def _register_and_login(client, email='lifestyle@example.com', username='lifestyleuser', password='password123'):
    res = client.post('/api/auth/register', json={
        'email': email,
        'username': username,
        'password': password,
        'consent_given': True,
    })
    assert res.status_code == 200
    return res.json()['access_token']


def _auth(token):
    return {'Authorization': f'Bearer {token}'}


LIFESTYLE_PAYLOAD = {
    'exercise_minutes': 30,
    'sleep_hours': 8.0,
    'stress_level': 2,
    'mood': 4,
    'sleep_quality': 4,
    'social_engagement': 3,
}


class TestLifestyleLog:
    def test_log_requires_auth(self, client):
        res = client.post('/api/lifestyle/log', json=LIFESTYLE_PAYLOAD)
        assert res.status_code == 401

    def test_log_lifestyle_success(self, client):
        token = _register_and_login(client)
        res = client.post('/api/lifestyle/log', json=LIFESTYLE_PAYLOAD, headers=_auth(token))
        assert res.status_code == 200
        data = res.json()
        assert data['exercise_minutes'] == 30
        assert data['sleep_hours'] == 8.0
        assert data['stress_level'] == 2
        assert data['mood'] == 4

    def test_log_lifestyle_upserts_same_day(self, client):
        token = _register_and_login(client)
        client.post('/api/lifestyle/log', json=LIFESTYLE_PAYLOAD, headers=_auth(token))
        updated = {**LIFESTYLE_PAYLOAD, 'exercise_minutes': 60}
        res = client.post('/api/lifestyle/log', json=updated, headers=_auth(token))
        assert res.status_code == 200
        assert res.json()['exercise_minutes'] == 60

    def test_get_today_requires_auth(self, client):
        res = client.get('/api/lifestyle/today')
        assert res.status_code == 401

    def test_get_today_404_when_no_log(self, client):
        token = _register_and_login(client)
        res = client.get('/api/lifestyle/today', headers=_auth(token))
        assert res.status_code == 404

    def test_get_today_returns_logged_data(self, client):
        token = _register_and_login(client)
        client.post('/api/lifestyle/log', json=LIFESTYLE_PAYLOAD, headers=_auth(token))
        res = client.get('/api/lifestyle/today', headers=_auth(token))
        assert res.status_code == 200
        assert res.json()['exercise_minutes'] == 30

    def test_get_history_requires_auth(self, client):
        res = client.get('/api/lifestyle/history')
        assert res.status_code == 401

    def test_get_history_empty_when_no_logs(self, client):
        token = _register_and_login(client)
        res = client.get('/api/lifestyle/history', headers=_auth(token))
        assert res.status_code == 200
        assert res.json() == []

    def test_get_history_returns_logged_data(self, client):
        token = _register_and_login(client)
        client.post('/api/lifestyle/log', json=LIFESTYLE_PAYLOAD, headers=_auth(token))
        res = client.get('/api/lifestyle/history', headers=_auth(token))
        assert res.status_code == 200
        assert len(res.json()) == 1

    def test_users_have_separate_logs(self, client):
        token_a = _register_and_login(client, 'a@lifestyle.com', 'userA')
        token_b = _register_and_login(client, 'b@lifestyle.com', 'userB')
        client.post('/api/lifestyle/log', json=LIFESTYLE_PAYLOAD, headers=_auth(token_a))
        res = client.get('/api/lifestyle/history', headers=_auth(token_b))
        assert res.json() == []
