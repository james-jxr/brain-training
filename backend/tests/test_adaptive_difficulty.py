import pytest
from backend.services import AdaptiveDifficultyService
from backend.database import SessionLocal, Base, engine
from backend.models import User, DomainProgress

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

def test_calculate_score():
    assert AdaptiveDifficultyService.calculate_score(8, 7) == 87.5
    assert AdaptiveDifficultyService.calculate_score(8, 8) == 100.0
    assert AdaptiveDifficultyService.calculate_score(8, 4) == 50.0
    assert AdaptiveDifficultyService.calculate_score(0, 0) == 0.0

def test_update_difficulty_high_score(test_db, test_user):
    progress = AdaptiveDifficultyService.update_difficulty(
        test_db,
        test_user.id,
        "processing_speed",
        85.0
    )
    assert progress.consecutive_correct == 1
    assert progress.consecutive_incorrect == 0
    assert progress.last_score == 85.0

def test_update_difficulty_three_consecutive_correct(test_db, test_user):
    for _ in range(3):
        AdaptiveDifficultyService.update_difficulty(
            test_db,
            test_user.id,
            "processing_speed",
            85.0
        )
    progress = test_db.query(DomainProgress).filter(
        DomainProgress.user_id == test_user.id,
        DomainProgress.domain == "processing_speed"
    ).first()
    assert progress.current_difficulty == 2

def test_update_difficulty_low_score(test_db, test_user):
    progress = AdaptiveDifficultyService.update_difficulty(
        test_db,
        test_user.id,
        "processing_speed",
        50.0
    )
    assert progress.consecutive_incorrect == 1
    assert progress.consecutive_correct == 0

def test_get_current_difficulty(test_db, test_user):
    difficulty = AdaptiveDifficultyService.get_current_difficulty(
        test_db,
        test_user.id,
        "processing_speed"
    )
    assert difficulty == 1

def test_is_at_ceiling_false(test_db, test_user):
    is_ceiling = AdaptiveDifficultyService.is_at_ceiling(
        test_db,
        test_user.id,
        "processing_speed"
    )
    assert is_ceiling is False

def test_is_at_ceiling_true(test_db, test_user):
    progress = DomainProgress(
        user_id=test_user.id,
        domain="processing_speed",
        current_difficulty=10,
        last_score=95.0
    )
    test_db.add(progress)
    test_db.commit()

    is_ceiling = AdaptiveDifficultyService.is_at_ceiling(
        test_db,
        test_user.id,
        "processing_speed"
    )
    assert is_ceiling is True
