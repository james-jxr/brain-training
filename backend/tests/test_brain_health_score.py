import pytest
from datetime import datetime, timedelta
from backend.services import BrainHealthScoreService
from backend.database import SessionLocal, Base, engine
from backend.models import User, DomainProgress, LifestyleLog

@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user(test_db):
    user = User(email="test@example.com", username="testuser", hashed_password="hashed")
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

def test_calculate_domain_average_no_scores(test_db, test_user):
    average = BrainHealthScoreService.calculate_domain_average(test_db, test_user.id)
    assert average == 0.0

def test_calculate_domain_average_with_scores(test_db, test_user):
    domains = ["processing_speed", "working_memory", "attention"]
    for i, domain in enumerate(domains):
        progress = DomainProgress(
            user_id=test_user.id,
            domain=domain,
            last_score=80.0 + i * 5
        )
        test_db.add(progress)
    test_db.commit()

    average = BrainHealthScoreService.calculate_domain_average(test_db, test_user.id)
    assert average == 85.0

def test_calculate_lifestyle_score_no_logs(test_db, test_user):
    score = BrainHealthScoreService.calculate_lifestyle_score(test_db, test_user.id)
    assert score == 0.0

def test_calculate_lifestyle_score_good_lifestyle(test_db, test_user):
    today = datetime.utcnow()
    log = LifestyleLog(
        user_id=test_user.id,
        logged_date=today.date(),
        exercise_minutes=30,
        sleep_hours=7,
        stress_level=2,
        mood=5
    )
    test_db.add(log)
    test_db.commit()

    score = BrainHealthScoreService.calculate_lifestyle_score(test_db, test_user.id)
    assert score >= 90.0

def test_calculate_brain_health_score(test_db, test_user):
    domains = ["processing_speed", "working_memory", "attention"]
    for i, domain in enumerate(domains):
        progress = DomainProgress(
            user_id=test_user.id,
            domain=domain,
            last_score=80.0 + i * 5
        )
        test_db.add(progress)

    today = datetime.utcnow()
    log = LifestyleLog(
        user_id=test_user.id,
        logged_date=today.date(),
        exercise_minutes=30,
        sleep_hours=7,
        stress_level=2,
        mood=5
    )
    test_db.add(log)
    test_db.commit()

    score = BrainHealthScoreService.calculate_brain_health_score(test_db, test_user.id)
    assert 0 <= score <= 100
    assert score > 80
