from sqlalchemy.orm import Session
from backend.models import Session as DBSession


def get_next_baseline_number(user_id: int, db: Session) -> int:
    """Return the next sequential baseline_number for the given user.

    Counts the existing baseline sessions for the user and returns COUNT + 1.
    This function must be called within the same database transaction as the
    session INSERT to prevent race conditions.
    """
    existing_count = db.query(DBSession).filter(
        DBSession.user_id == user_id,
        DBSession.is_baseline == True
    ).count()
    return existing_count + 1
