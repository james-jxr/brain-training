from sqlalchemy.orm import Session
from sqlalchemy import and_
from backend.models import DomainProgress, LifestyleLog
from datetime import datetime, timedelta, timezone, date

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
            if log.exercise_minutes >= 30:
                exercise_score += 25
            else:
                exercise_score += (log.exercise_minutes / 30) * 25

            if log.sleep_hours >= 7:
                sleep_score += 25
            else:
                sleep_score += (log.sleep_hours / 7) * 25

            if log.stress_level <= 2:
                stress_score += 25
            else:
                stress_score += max(0, (5 - log.stress_level) / 3 * 25)

            if log.mood >= 4:
                mood_score += 25
            else:
                mood_score += (log.mood / 5) * 25

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

        brain_health = (domain_avg * 0.6) + (lifestyle_score * 0.4)

        return int(min(100, max(0, brain_health)))
