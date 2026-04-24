from sqlalchemy.orm import Session
from backend.models import DomainProgress, ExerciseAttempt
from sqlalchemy import desc, and_
from datetime import datetime, timezone


def adjust_difficulty_in_session(current_difficulty: int, last_score: float) -> int:
    """Simple staircase rule for within-session difficulty adaptation.

    - If the user scored above 80% on the last exercise, increase difficulty by 1.
    - If below 50%, decrease difficulty by 1.
    - Otherwise keep the same.
    - Clamps result to [1, 10].
    """
    if last_score > 80:
        new_difficulty = current_difficulty + 1
    elif last_score < 50:
        new_difficulty = current_difficulty - 1
    else:
        new_difficulty = current_difficulty
    return max(1, min(10, new_difficulty))


class AdaptiveDifficultyService:
    @staticmethod
    def calculate_score(trials_presented: int, trials_correct: int) -> float:
        if trials_presented == 0:
            return 0.0
        return (trials_correct / trials_presented) * 100

    @staticmethod
    def update_difficulty(db: Session, user_id: int, domain: str, latest_score: float):
        progress = db.query(DomainProgress).filter(
            and_(
                DomainProgress.user_id == user_id,
                DomainProgress.domain == domain
            )
        ).first()

        if not progress:
            progress = DomainProgress(
                user_id=user_id,
                domain=domain,
                current_difficulty=1,
                consecutive_correct=0,
                consecutive_incorrect=0,
                last_score=latest_score
            )
            db.add(progress)
            db.commit()
            db.refresh(progress)

        progress.last_score = latest_score

        if latest_score > 80:
            progress.consecutive_correct += 1
            progress.consecutive_incorrect = 0
        else:
            progress.consecutive_incorrect += 1
            progress.consecutive_correct = 0

        if progress.consecutive_correct >= 3 and progress.current_difficulty < 10:
            progress.current_difficulty += 1
            progress.consecutive_correct = 0

        if progress.consecutive_incorrect >= 1 and progress.current_difficulty > 1:
            if latest_score < 70:
                progress.current_difficulty = max(1, progress.current_difficulty - 1)
                progress.consecutive_incorrect = 0

        progress.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(progress)

        return progress

    @staticmethod
    def get_current_difficulty(db: Session, user_id: int, domain: str) -> int:
        progress = db.query(DomainProgress).filter(
            and_(
                DomainProgress.user_id == user_id,
                DomainProgress.domain == domain
            )
        ).first()

        if not progress:
            progress = DomainProgress(
                user_id=user_id,
                domain=domain,
                current_difficulty=1
            )
            db.add(progress)
            db.commit()
            db.refresh(progress)

        return progress.current_difficulty

    @staticmethod
    def is_at_ceiling(db: Session, user_id: int, domain: str) -> bool:
        progress = db.query(DomainProgress).filter(
            and_(
                DomainProgress.user_id == user_id,
                DomainProgress.domain == domain
            )
        ).first()

        if not progress:
            return False

        if progress.current_difficulty < 10:
            return False

        if progress.last_score is None or progress.last_score <= 90:
            return False

        return True
