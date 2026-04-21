from sqlalchemy.orm import Session
from backend.models import Streak
from datetime import datetime, timedelta, timezone

class StreakManagerService:
    @staticmethod
    def get_or_create_streak(db: Session, user_id: int) -> Streak:
        streak = db.query(Streak).filter(Streak.user_id == user_id).first()

        if not streak:
            streak = Streak(user_id=user_id, current_streak=0, longest_streak=0)
            db.add(streak)
            db.commit()
            db.refresh(streak)

        return streak

    @staticmethod
    def update_streak(db: Session, user_id: int) -> Streak:
        streak = StreakManagerService.get_or_create_streak(db, user_id)
        now = datetime.now(timezone.utc)

        if streak.last_session_date is None:
            streak.current_streak = 1
        else:
            last_session = streak.last_session_date
            if last_session.tzinfo is None:
                last_session = last_session.replace(tzinfo=timezone.utc)
            time_since_last = now - last_session
            hours_since = time_since_last.total_seconds() / 3600

            if hours_since > 36:
                streak.current_streak = 1
            elif last_session.date() == now.date():
                pass
            else:
                streak.current_streak += 1

        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak

        streak.last_session_date = now
        streak.updated_at = now

        db.commit()
        db.refresh(streak)

        return streak

    @staticmethod
    def get_current_streak(db: Session, user_id: int) -> int:
        streak = StreakManagerService.get_or_create_streak(db, user_id)

        if streak.last_session_date is None:
            return 0

        now = datetime.now(timezone.utc)
        last_session = streak.last_session_date
        if last_session.tzinfo is None:
            last_session = last_session.replace(tzinfo=timezone.utc)
        time_since_last = now - last_session
        hours_since = time_since_last.total_seconds() / 3600

        if hours_since > 36:
            return 0

        return streak.current_streak

    @staticmethod
    def get_longest_streak(db: Session, user_id: int) -> int:
        streak = StreakManagerService.get_or_create_streak(db, user_id)
        return streak.longest_streak