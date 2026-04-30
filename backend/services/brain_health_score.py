from sqlalchemy.orm import Session
from sqlalchemy import and_
from backend.models import DomainProgress, LifestyleLog
from datetime import datetime, timedelta, timezone, date

DOMAIN_SCORE_WEIGHT = 0.6
LIFESTYLE_SCORE_WEIGHT = 0.4
TARGET_EXERCISE_MINUTES = 30
TARGET_SLEEP_HOURS = 7
MAX_LIFESTYLE_FACTOR_SCORE = 25
STRESS_LOW_THRESHOLD = 2
STRESS_HIGH_THRESHOLD = 5
STRESS_SCORE_DIVISOR = 3
MOOD_THRESHOLD = 4
MOOD_SCALE_MAX = 5


class BrainHealthScoreService:
    @staticmethod
    def calculate_domain_average(db: Session, user_id: int) -> float:
        domains = ["processing_speed", "working_memory", "attention"]
        scores = []

        for domain in domains:
            progress = db.query(DomainProgress).filter(
                and_(
                    DomainProgress.user_id == user_id,
                    DomainProgress.domain == domain
                )
            ).first()

            if progress and progress.last_score is not None:
                scores.append(progress.last_score)

        if not scores:
            return 0.0

        return sum(scores) / len(scores)

    @staticmethod
    def calculate_lifestyle_score(db: Session, user_id: int) -> float:
        seven_days_ago = date.today() - timedelta(days=7)
        logs = db.query(LifestyleLog).filter(
            and_(
                LifestyleLog.user_id == user_id,
                LifestyleLog.logged_date >= seven_days_ago
            )
        ).all()

        if not logs:
            return 0.0

        exercise_score = 0
        sleep_score = 0
        stress_score = 0
        mood_score = 0
        count = len(logs)

        for log in logs:
            if log.exercise_minutes >= TARGET_EXERCISE_MINUTES:
                exercise_score += MAX_LIFESTYLE_FACTOR_SCORE
            else:
                exercise_score += (log.exercise_minutes / TARGET_EXERCISE_MINUTES) * MAX_LIFESTYLE_FACTOR_SCORE

            if log.sleep_hours >= TARGET_SLEEP_HOURS:
                sleep_score += MAX_LIFESTYLE_FACTOR_SCORE
            else:
                sleep_score += (log.sleep_hours / TARGET_SLEEP_HOURS) * MAX_LIFESTYLE_FACTOR_SCORE

            if log.stress_level <= STRESS_LOW_THRESHOLD:
                stress_score += MAX_LIFESTYLE_FACTOR_SCORE
            else:
                stress_score += max(0, (STRESS_HIGH_THRESHOLD - log.stress_level) / STRESS_SCORE_DIVISOR * MAX_LIFESTYLE_FACTOR_SCORE)

            if log.mood >= MOOD_THRESHOLD:
                mood_score += MAX_LIFESTYLE_FACTOR_SCORE
            else:
                mood_score += (log.mood / MOOD_SCALE_MAX) * MAX_LIFESTYLE_FACTOR_SCORE

        avg_exercise = exercise_score / count
        avg_sleep = sleep_score / count
        avg_stress = stress_score / count
        avg_mood = mood_score / count

        # Each factor contributes up to 25 points; total scores out of 100
        lifestyle_score = avg_exercise + avg_sleep + avg_stress + avg_mood

        return min(100, lifestyle_score)

    @staticmethod
    def calculate_brain_health_score(db: Session, user_id: int) -> int:
        domain_avg = BrainHealthScoreService.calculate_domain_average(db, user_id)
        lifestyle_score = BrainHealthScoreService.calculate_lifestyle_score(db, user_id)

        brain_health = (domain_avg * DOMAIN_SCORE_WEIGHT) + (lifestyle_score * LIFESTYLE_SCORE_WEIGHT)

        return int(min(100, max(0, brain_health)))
