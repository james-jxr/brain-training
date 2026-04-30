import os
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-ci')
os.environ.setdefault('DATABASE_URL', 'sqlite:///./test.db')

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


def _register(client, email='sess@example.com', username='sessuser', password='password123'):
    res = client.post('/api/auth/register', json={
        'email': email,
        'username': username,
        'password': password,
        'consent_given': True,
    })
    assert res.status_code == 200, res.text
    return res.json()['access_token']


def _auth(token):
    return {'Authorization': f'Bearer {token}'}


def _start_session(client, token, domain_1='working_memory', domain_2='attention'):
    res = client.post('/api/sessions/start', json={
        'domain_1': domain_1,
        'domain_2': domain_2,
    }, headers=_auth(token))
    assert res.status_code == 200, res.text
    return res.json()['id']


class TestStartSession:
    def test_start_session_requires_auth(self, client):
        res = client.post('/api/sessions/start', json={
            'domain_1': 'working_memory',
            'domain_2': 'attention',
        })
        assert res.status_code == 401

    def test_start_session_returns_id(self, client):
        token = _register(client)
        session_id = _start_session(client, token)
        assert isinstance(session_id, int)
        assert session_id > 0

    def test_start_session_stores_domains(self, client):
        token = _register(client)
        res = client.post('/api/sessions/start', json={
            'domain_1': 'working_memory',
            'domain_2': 'attention',
        }, headers=_auth(token))
        assert res.status_code == 200
        data = res.json()
        assert data['domain_1'] == 'working_memory'
        assert data['domain_2'] == 'attention'


class TestLogExerciseResult:
    def test_log_result_requires_auth(self, client):
        res = client.post('/api/sessions/1/exercise-result', json={
            'domain': 'working_memory',
            'exercise_type': 'n_back',
            'trials_presented': 10,
            'trials_correct': 8,
            'avg_response_ms': 500,
            'difficulty': '3',
        })
        assert res.status_code == 401

    def test_log_result_returns_accuracy(self, client):
        token = _register(client)
        session_id = _start_session(client, token)
        res = client.post(f'/api/sessions/{session_id}/exercise-result', json={
            'domain': 'working_memory',
            'exercise_type': 'n_back',
            'trials_presented': 10,
            'trials_correct': 8,
            'avg_response_ms': 500,
            'difficulty': '3',
        }, headers=_auth(token))
        assert res.status_code == 200
        data = res.json()
        assert data['accuracy_score'] == 80.0

    def test_log_result_returns_adjusted_difficulty(self, client):
        token = _register(client)
        session_id = _start_session(client, token)
        res = client.post(f'/api/sessions/{session_id}/exercise-result', json={
            'domain': 'working_memory',
            'exercise_type': 'n_back',
            'trials_presented': 10,
            'trials_correct': 9,
            'avg_response_ms': 400,
            'difficulty': '5',
        }, headers=_auth(token))
        assert res.status_code == 200
        data = res.json()
        assert 'adjusted_difficulty' in data
        assert isinstance(data['adjusted_difficulty'], int)

    def test_log_result_invalid_session_returns_404(self, client):
        token = _register(client)
        res = client.post('/api/sessions/99999/exercise-result', json={
            'domain': 'working_memory',
            'exercise_type': 'n_back',
            'trials_presented': 10,
            'trials_correct': 8,
            'avg_response_ms': 500,
            'difficulty': '3',
        }, headers=_auth(token))
        assert res.status_code == 404

    def test_log_card_memory_result(self, client):
        token = _register(client)
        session_id = _start_session(client, token, 'episodic_memory', 'attention')
        res = client.post(f'/api/sessions/{session_id}/exercise-result', json={
            'domain': 'episodic_memory',
            'exercise_type': 'card_memory',
            'difficulty': '3',
            'card_count': 4,
            'correct': True,
            'response_time_ms': 3000,
            'score': 90,
            'trials_presented': 1,
            'trials_correct': 1,
            'avg_response_ms': 3000,
        }, headers=_auth(token))
        assert res.status_code == 200
        data = res.json()
        assert data['accuracy_score'] == 100.0

    def test_log_zero_trials_returns_zero_accuracy(self, client):
        token = _register(client)
        session_id = _start_session(client, token)
        res = client.post(f'/api/sessions/{session_id}/exercise-result', json={
            'domain': 'working_memory',
            'exercise_type': 'n_back',
            'trials_presented': 0,
            'trials_correct': 0,
            'avg_response_ms': 0,
            'difficulty': '1',
        }, headers=_auth(token))
        assert res.status_code == 200
        assert res.json()['accuracy_score'] == 0.0


class TestCompleteSession:
    def test_complete_session_requires_auth(self, client):
        res = client.post('/api/sessions/1/complete')
        assert res.status_code == 401

    def test_complete_session_success(self, client):
        token = _register(client)
        session_id = _start_session(client, token)
        res = client.post(f'/api/sessions/{session_id}/complete', headers=_auth(token))
        assert res.status_code == 200
        data = res.json()
        assert data['session_id'] == session_id
        assert 'completed_at' in data

    def test_complete_invalid_session_returns_404(self, client):
        token = _register(client)
        res = client.post('/api/sessions/99999/complete', headers=_auth(token))
        assert res.status_code == 404


class TestGetSession:
    def test_get_session_requires_auth(self, client):
        res = client.get('/api/sessions/1')
        assert res.status_code == 401

    def test_get_session_returns_data(self, client):
        token = _register(client)
        session_id = _start_session(client, token)
        res = client.get(f'/api/sessions/{session_id}', headers=_auth(token))
        assert res.status_code == 200
        data = res.json()
        assert data['id'] == session_id

    def test_get_session_not_found(self, client):
        token = _register(client)
        res = client.get('/api/sessions/99999', headers=_auth(token))
        assert res.status_code == 404


class TestListSessions:
    def test_list_sessions_requires_auth(self, client):
        res = client.get('/api/sessions')
        assert res.status_code == 401

    def test_list_sessions_empty_initially(self, client):
        token = _register(client)
        res = client.get('/api/sessions', headers=_auth(token))
        assert res.status_code == 200
        assert res.json() == []

    def test_list_sessions_returns_created_sessions(self, client):
        token = _register(client)
        _start_session(client, token)
        _start_session(client, token)
        res = client.get('/api/sessions', headers=_auth(token))
        assert res.status_code == 200
        assert len(res.json()) == 2


class TestExtractAccuracy:
    """Unit tests for the extract_accuracy helper logic (tested via API)."""

    def test_perfect_score(self, client):
        token = _register(client)
        session_id = _start_session(client, token)
        res = client.post(f'/api/sessions/{session_id}/exercise-result', json={
            'domain': 'attention',
            'exercise_type': 'stroop',
            'trials_presented': 5,
            'trials_correct': 5,
            'avg_response_ms': 300,
            'difficulty': '4',
        }, headers=_auth(token))
        assert res.json()['accuracy_score'] == 100.0

    def test_zero_score(self, client):
        token = _register(client)
        session_id = _start_session(client, token)
        res = client.post(f'/api/sessions/{session_id}/exercise-result', json={
            'domain': 'attention',
            'exercise_type': 'stroop',
            'trials_presented': 5,
            'trials_correct': 0,
            'avg_response_ms': 300,
            'difficulty': '4',
        }, headers=_auth(token))
        assert res.json()['accuracy_score'] == 0.0

    def test_partial_score(self, client):
        token = _register(client)
        session_id = _start_session(client, token)
        res = client.post(f'/api/sessions/{session_id}/exercise-result', json={
            'domain': 'attention',
            'exercise_type': 'go_no_go',
            'trials_presented': 4,
            'trials_correct': 3,
            'avg_response_ms': 450,
            'difficulty': '2',
        }, headers=_auth(token))
        assert res.json()['accuracy_score'] == 75.0
