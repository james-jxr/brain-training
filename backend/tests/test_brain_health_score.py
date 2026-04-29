import pytest
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
from backend.models import User, DomainProgress, LifestyleLog
from backend.services.brain_health_score import BrainHealthScoreService

TEST_DATABASE_URL = 'sqlite:///./test_bhs.db'

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
    u = User(email='bhs@example.com', username='bhsuser', hashed_password='hashed')
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


class TestCalculateDomainAverage:
    def test_returns_0_when_no_domain_progress(self, db, user):
        result = BrainHealthScoreService.calculate_domain_average(db, user.id)
        assert result == 0.0

    def test_returns_single_domain_score(self, db, user):
        dp = DomainProgress(
            user_id=user.id,
            domain='processing_speed',
            current_difficulty=1,
            last_score=80.0,
        )
        db.add(dp)
        db.commit()
        result = BrainHealthScoreService.calculate_domain_average(db, user.id)
        assert result == 80.0

    def test_averages_multiple_domains(self, db, user):
        for domain, score in [('processing_speed', 60.0), ('working_memory', 80.0), ('attention', 100.0)]:
            db.add(DomainProgress(
                user_id=user.id,
                domain=domain,
                current_difficulty=1,
                last_score=score,
            ))
        db.commit()
        result = BrainHealthScoreService.calculate_domain_average(db, user.id)
        assert pytest.approx(result) == 80.0

    def test_ignores_domains_with_null_score(self, db, user):
        dp = DomainProgress(
            user_id=user.id,
            domain='processing_speed',
            current_difficulty=1,
            last_score=None,
        )
        db.add(dp)
        db.commit()
        result = BrainHealthScoreService.calculate_domain_average(db, user.id)
        assert result == 0.0


class TestCalculateLifestyleScore:
    def test_returns_0_when_no_logs(self, db, user):
        result = BrainHealthScoreService.calculate_lifestyle_score(db, user.id)
        assert result == 0.0

    def test_perfect_lifestyle_returns_100(self, db, user):
        log = LifestyleLog(
            user_id=user.id,
            logged_date=date.today(),
            exercise_minutes=30,
            sleep_hours=7.0,
            stress_level=2,
            mood=4,
            sleep_quality=4,
            social_engagement=3,
        )
        db.add(log)
        db.commit()
        result = BrainHealthScoreService.calculate_lifestyle_score(db, user.id)
        # 25 (exercise) + 25 (sleep) + 25 (stress<=2) + 25 (mood>=4) = 100
        assert result == 100.0

    def test_zero_values_return_low_score(self, db, user):
        log = LifestyleLog(
            user_id=user.id,
            logged_date=date.today(),
            exercise_minutes=0,
            sleep_hours=0,
            stress_level=5,
            mood=0,
            sleep_quality=1,
            social_engagement=1,
        )
        db.add(log)
        db.commit()
        result = BrainHealthScoreService.calculate_lifestyle_score(db, user.id)
        assert result < 25.0

    def test_score_capped_at_100(self, db, user):
        # Insert multiple perfect logs
        for i in range(7):
            log = LifestyleLog(
                user_id=user.id,
                logged_date=date.today() - timedelta(days=i),
                exercise_minutes=60,
                sleep_hours=9.0,
                stress_level=1,
                mood=5,
                sleep_quality=5,
                social_engagement=5,
            )
            db.add(log)
        db.commit()
        result = BrainHealthScoreService.calculate_lifestyle_score(db, user.id)
        assert result <= 100.0

    def test_ignores_logs_older_than_7_days(self, db, user):
        old_log = LifestyleLog(
            user_id=user.id,
            logged_date=date.today() - timedelta(days=8),
            exercise_minutes=60,
            sleep_hours=9.0,
            stress_level=1,
            mood=5,
            sleep_quality=5,
            social_engagement=5,
        )
        db.add(old_log)
        db.commit()
        result = BrainHealthScoreService.calculate_lifestyle_score(db, user.id)
        assert result == 0.0


class TestCalculateBrainHealthScore:
    def test_returns_0_for_new_user(self, db, user):
        result = BrainHealthScoreService.calculate_brain_health_score(db, user.id)
        assert result == 0

    def test_combines_domain_and_lifestyle_scores(self, db, user):
        # Domain score: 100.0
        for domain in ['processing_speed', 'working_memory', 'attention']:
            db.add(DomainProgress(
                user_id=user.id,
                domain=domain,
                current_difficulty=1,
                last_score=100.0,
            ))
        # Lifestyle score: 100.0
        db.add(LifestyleLog(
            user_id=user.id,
            logged_date=date.today(),
            exercise_minutes=30,
            sleep_hours=7.0,
            stress_level=2,
            mood=4,
            sleep_quality=4,
            social_engagement=3,
        ))
        db.commit()

        result = BrainHealthScoreService.calculate_brain_health_score(db, user.id)
        # 100 * 0.6 + 100 * 0.4 = 100
        assert result == 100

    def test_result_is_int(self, db, user):
        result = BrainHealthScoreService.calculate_brain_health_score(db, user.id)
        assert isinstance(result, int)

    def test_result_capped_at_100(self, db, user):
        for domain in ['processing_speed', 'working_memory', 'attention']:
            db.add(DomainProgress(
                user_id=user.id,
                domain=domain,
                current_difficulty=1,
                last_score=100.0,
            ))
        db.add(LifestyleLog(
            user_id=user.id,
            logged_date=date.today(),
            exercise_minutes=30,
            sleep_hours=7.0,
            stress_level=1,
            mood=5,
            sleep_quality=5,
            social_engagement=5,
        ))
        db.commit()
        result = BrainHealthScoreService.calculate_brain_health_score(db, user.id)
        assert result <= 100

    def test_result_minimum_0(self, db, user):
        result = BrainHealthScoreService.calculate_brain_health_score(db, user.id)
        assert result >= 0

    def test_domain_weighted_60_percent(self, db, user):
        # Only domain scores, no lifestyle
        for domain in ['processing_speed', 'working_memory', 'attention']:
            db.add(DomainProgress(
                user_id=user.id,
                domain=domain,
                current_difficulty=1,
                last_score=100.0,
            ))
        db.commit()
        result = BrainHealthScoreService.calculate_brain_health_score(db, user.id)
        # domain_avg=100, lifestyle=0 -> 100*0.6 + 0*0.4 = 60
        assert result == 60
