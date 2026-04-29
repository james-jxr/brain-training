import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import User, Streak
from backend.services.streak_manager import StreakManagerService, STREAK_EXPIRY_HOURS

TEST_DATABASE_URL = 'sqlite:///./test_streak.db'

engine = create_engine(TEST_DATABASE_URL, connect_args={'check_same_thread': False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope='function')
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def user(db):
    u = User(email='streak@example.com', username='streakuser', hashed_password='hashed')
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


class TestGetOrCreateStreak:
    def test_creates_streak_for_new_user(self, db, user):
        streak = StreakManagerService.get_or_create_streak(db, user.id)
        assert streak is not None
        assert streak.user_id == user.id
        assert streak.current_streak == 0
        assert streak.longest_streak == 0

    def test_returns_existing_streak(self, db, user):
        s1 = StreakManagerService.get_or_create_streak(db, user.id)
        s2 = StreakManagerService.get_or_create_streak(db, user.id)
        assert s1.id == s2.id

    def test_does_not_duplicate_streak(self, db, user):
        StreakManagerService.get_or_create_streak(db, user.id)
        StreakManagerService.get_or_create_streak(db, user.id)
        count = db.query(Streak).filter(Streak.user_id == user.id).count()
        assert count == 1


class TestUpdateStreak:
    def test_first_session_sets_streak_to_1(self, db, user):
        streak = StreakManagerService.update_streak(db, user.id)
        assert streak.current_streak == 1

    def test_first_session_sets_longest_streak_to_1(self, db, user):
        streak = StreakManagerService.update_streak(db, user.id)
        assert streak.longest_streak == 1

    def test_second_session_same_day_does_not_increment(self, db, user):
        streak = StreakManagerService.update_streak(db, user.id)
        # Set last_session_date to today explicitly
        streak.last_session_date = datetime.now(timezone.utc)
        db.commit()
        streak2 = StreakManagerService.update_streak(db, user.id)
        assert streak2.current_streak == 1

    def test_session_next_day_increments_streak(self, db, user):
        streak = StreakManagerService.get_or_create_streak(db, user.id)
        # Set last session to yesterday
        yesterday = datetime.now(timezone.utc) - timedelta(hours=25)
        streak.current_streak = 1
        streak.longest_streak = 1
        streak.last_session_date = yesterday
        db.commit()

        updated = StreakManagerService.update_streak(db, user.id)
        assert updated.current_streak == 2

    def test_session_after_expiry_resets_streak(self, db, user):
        streak = StreakManagerService.get_or_create_streak(db, user.id)
        # Set last session beyond expiry window
        old_date = datetime.now(timezone.utc) - timedelta(hours=STREAK_EXPIRY_HOURS + 1)
        streak.current_streak = 5
        streak.longest_streak = 5
        streak.last_session_date = old_date
        db.commit()

        updated = StreakManagerService.update_streak(db, user.id)
        assert updated.current_streak == 1

    def test_longest_streak_updated_when_current_exceeds(self, db, user):
        streak = StreakManagerService.get_or_create_streak(db, user.id)
        streak.current_streak = 4
        streak.longest_streak = 4
        streak.last_session_date = datetime.now(timezone.utc) - timedelta(hours=25)
        db.commit()

        updated = StreakManagerService.update_streak(db, user.id)
        assert updated.longest_streak == 5

    def test_longest_streak_not_decreased(self, db, user):
        streak = StreakManagerService.get_or_create_streak(db, user.id)
        old_date = datetime.now(timezone.utc) - timedelta(hours=STREAK_EXPIRY_HOURS + 1)
        streak.current_streak = 10
        streak.longest_streak = 10
        streak.last_session_date = old_date
        db.commit()

        updated = StreakManagerService.update_streak(db, user.id)
        assert updated.current_streak == 1
        assert updated.longest_streak == 10

    def test_update_sets_last_session_date(self, db, user):
        before = datetime.now(timezone.utc)
        streak = StreakManagerService.update_streak(db, user.id)
        assert streak.last_session_date is not None
        # last_session_date should be >= before
        last = streak.last_session_date
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        assert last >= before

    def test_naive_last_session_date_handled(self, db, user):
        streak = StreakManagerService.get_or_create_streak(db, user.id)
        # Store naive datetime (no tzinfo)
        streak.last_session_date = datetime.utcnow() - timedelta(hours=25)
        streak.current_streak = 1
        streak.longest_streak = 1
        db.commit()

        updated = StreakManagerService.update_streak(db, user.id)
        assert updated.current_streak == 2


class TestGetCurrentStreak:
    def test_returns_0_with_no_sessions(self, db, user):
        result = StreakManagerService.get_current_streak(db, user.id)
        assert result == 0

    def test_returns_current_streak_when_active(self, db, user):
        streak = StreakManagerService.get_or_create_streak(db, user.id)
        streak.current_streak = 7
        streak.last_session_date = datetime.now(timezone.utc)
        db.commit()

        result = StreakManagerService.get_current_streak(db, user.id)
        assert result == 7

    def test_returns_0_when_streak_expired(self, db, user):
        streak = StreakManagerService.get_or_create_streak(db, user.id)
        streak.current_streak = 5
        streak.last_session_date = datetime.now(timezone.utc) - timedelta(hours=STREAK_EXPIRY_HOURS + 1)
        db.commit()

        result = StreakManagerService.get_current_streak(db, user.id)
        assert result == 0

    def test_handles_naive_last_session_date(self, db, user):
        streak = StreakManagerService.get_or_create_streak(db, user.id)
        streak.current_streak = 3
        streak.last_session_date = datetime.utcnow()  # naive
        db.commit()

        result = StreakManagerService.get_current_streak(db, user.id)
        assert result == 3


class TestGetLongestStreak:
    def test_returns_0_for_new_user(self, db, user):
        result = StreakManagerService.get_longest_streak(db, user.id)
        assert result == 0

    def test_returns_longest_streak_value(self, db, user):
        streak = StreakManagerService.get_or_create_streak(db, user.id)
        streak.longest_streak = 15
        db.commit()

        result = StreakManagerService.get_longest_streak(db, user.id)
        assert result == 15
