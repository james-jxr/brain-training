import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_db, init_db, Base, engine
from backend.models import User, Session as DBSession, ExerciseAttempt
from sqlalchemy.orm import Session
from datetime import datetime
import json

client = TestClient(app)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_user(db_session):
    user = User(
        email="cardmemory@test.com",
        hashed_password="hashedpass",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_session(db_session, test_user):
    session = DBSession(
        user_id=test_user.id,
        domain_1="episodic_memory",
        domain_2="processing_speed",
        is_baseline=0
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session

def test_card_memory_result_easy_correct(db_session, test_session, monkeypatch):
    monkeypatch.setenv("TESTING", "true")

    payload = {
        "domain": "episodic_memory",
        "exercise_type": "card_memory",
        "difficulty": "easy",
        "card_count": 4,
        "correct": True,
        "response_time_ms": 2500,
        "score": 180
    }

    attempts_before = db_session.query(ExerciseAttempt).count()

    attempt = ExerciseAttempt(
        session_id=test_session.id,
        domain=payload["domain"],
        exercise_type=payload["exercise_type"],
        difficulty=payload["difficulty"],
        card_count=payload["card_count"],
        correct=payload["correct"],
        response_time_ms=payload["response_time_ms"],
        score=payload["score"]
    )
    db_session.add(attempt)
    db_session.commit()
    db_session.refresh(attempt)

    assert attempt.id is not None
    assert attempt.exercise_type == "card_memory"
    assert attempt.correct == True
    assert attempt.score == 180
    assert attempt.difficulty == "easy"

def test_card_memory_result_hard_incorrect(db_session, test_session):
    payload = {
        "domain": "episodic_memory",
        "exercise_type": "card_memory",
        "difficulty": "hard",
        "card_count": 12,
        "correct": False,
        "response_time_ms": 4500,
        "score": 25
    }

    attempt = ExerciseAttempt(
        session_id=test_session.id,
        domain=payload["domain"],
        exercise_type=payload["exercise_type"],
        difficulty=payload["difficulty"],
        card_count=payload["card_count"],
        correct=payload["correct"],
        response_time_ms=payload["response_time_ms"],
        score=payload["score"]
    )
    db_session.add(attempt)
    db_session.commit()
    db_session.refresh(attempt)

    assert attempt.id is not None
    assert attempt.correct == False
    assert attempt.score == 25
    assert attempt.difficulty == "hard"
    assert attempt.card_count == 12

def test_card_memory_result_medium(db_session, test_session):
    payload = {
        "domain": "episodic_memory",
        "exercise_type": "card_memory",
        "difficulty": "medium",
        "card_count": 8,
        "correct": True,
        "response_time_ms": 3200,
        "score": 145
    }

    attempt = ExerciseAttempt(
        session_id=test_session.id,
        domain=payload["domain"],
        exercise_type=payload["exercise_type"],
        difficulty=payload["difficulty"],
        card_count=payload["card_count"],
        correct=payload["correct"],
        response_time_ms=payload["response_time_ms"],
        score=payload["score"]
    )
    db_session.add(attempt)
    db_session.commit()
    db_session.refresh(attempt)

    assert attempt.difficulty == "medium"
    assert attempt.card_count == 8
    assert attempt.correct == True

def test_exercise_attempt_backward_compatibility(db_session, test_session):
    old_style_attempt = ExerciseAttempt(
        session_id=test_session.id,
        domain="processing_speed",
        exercise_type="symbol_matching",
        trials_presented=8,
        trials_correct=7,
        avg_response_ms=1250.5
    )
    db_session.add(old_style_attempt)
    db_session.commit()
    db_session.refresh(old_style_attempt)

    assert old_style_attempt.id is not None
    assert old_style_attempt.trials_presented == 8
    assert old_style_attempt.trials_correct == 7
    assert old_style_attempt.difficulty is None
    assert old_style_attempt.correct is None
