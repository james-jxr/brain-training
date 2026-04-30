from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from backend.database import get_db
from backend.models import User, Session as DBSession, ExerciseAttempt, DomainProgress
from backend.schemas import SessionCreate, SessionResponse, ExerciseAttemptCreate, ExerciseAttemptResponse
from backend.security import get_current_user
from backend.services import AdaptiveDifficultyService, StreakManagerService, SessionPlannerService
from backend.services.adaptive_difficulty import adjust_difficulty_in_session
from backend.services.session_helpers import get_next_baseline_number

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def extract_accuracy(attempt: ExerciseAttemptCreate) -> tuple[float, int, int]:
    """Extract accuracy_score, trials_presented, and trials_correct from an exercise attempt.

    For card_memory exercises, trials_presented defaults to 1 and trials_correct
    defaults based on the correct flag. For all other exercise types, trials_presented
    and trials_correct are taken directly from the payload (defaulting to 0).

    Returns:
        A tuple of (accuracy_score, trials_presented, trials_correct).
    """
    if attempt.exercise_type == "card_memory":
        trials_presented = attempt.trials_presented or 1
        trials_correct = attempt.trials_correct or (1 if attempt.correct else 0)
        if trials_presented > 0:
            accuracy_score = (trials_correct / trials_presented) * 100
        else:
            accuracy_score = 0.0
    else:
        trials_presented = attempt.trials_presented or 0
        trials_correct = attempt.trials_correct or 0
        if trials_presented > 0:
            accuracy_score = (trials_correct / trials_presented) * 100
        else:
            accuracy_score = 0.0
    return accuracy_score, trials_presented, trials_correct


@router.post("/start", response_model=SessionResponse)
def start_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if session_data.is_baseline:
        baseline_number = get_next_baseline_number(current_user.id, db)
    else:
        baseline_number = None

    new_session = DBSession(
        user_id=current_user.id,
        domain_1=session_data.domain_1,
        domain_2=session_data.domain_2,
        is_baseline=session_data.is_baseline,
        baseline_number=baseline_number
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return SessionResponse.model_validate(new_session)

@router.post("/{session_id}/exercise-result")
def log_exercise_result(
    session_id: int,
    exercise_data: ExerciseAttemptCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail={"message": "Session not found"})

    attempt = ExerciseAttempt(
        session_id=session_id,
        domain=exercise_data.domain,
        exercise_type=exercise_data.exercise_type,
        trials_presented=exercise_data.trials_presented,
        trials_correct=exercise_data.trials_correct,
        avg_response_ms=exercise_data.avg_response_ms,
        difficulty=exercise_data.difficulty,
        card_count=exercise_data.card_count,
        correct=exercise_data.correct,
        response_time_ms=exercise_data.response_time_ms,
        score=exercise_data.score
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    accuracy_score, trials_presented, trials_correct = extract_accuracy(exercise_data)

    progress = db.query(DomainProgress).filter(
        DomainProgress.user_id == current_user.id,
        DomainProgress.domain == exercise_data.domain
    ).first()

    if progress:
        progress.total_attempts = (progress.total_attempts or 0) + trials_presented
        progress.total_correct = (progress.total_correct or 0) + trials_correct
        db.commit()

    # update_difficulty commits current_difficulty to the DB before the next
    # exercise is loaded, ensuring cross-session persistence.
    updated_progress = AdaptiveDifficultyService.update_difficulty(
        db,
        current_user.id,
        exercise_data.domain,
        accuracy_score
    )

    # Compute in-session adjusted difficulty using the 2-up/1-down staircase rule.
    # Read consecutive_correct from the freshly-committed progress record so that
    # the staircase always operates on the current persisted state.
    current_difficulty_int = updated_progress.current_difficulty if updated_progress else 1
    consecutive_correct = updated_progress.consecutive_correct if updated_progress else 0

    adjusted_difficulty = adjust_difficulty_in_session(
        current_difficulty_int,
        accuracy_score,
        consecutive_correct
    )

    response = ExerciseAttemptResponse.model_validate(attempt)
    return {
        **response.model_dump(),
        "accuracy_score": round(accuracy_score, 2),
        "adjusted_difficulty": adjusted_difficulty
    }

@router.post("/{session_id}/complete")
def complete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail={"message": "Session not found"})

    session.completed_at = datetime.now(timezone.utc)
    db.commit()

    StreakManagerService.update_streak(db, current_user.id)

    return {
        "message": "Session completed",
        "session_id": session_id,
        "completed_at": session.completed_at
    }

@router.get("/{session_id}/next")
def get_next_exercise(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail={"message": "Session not found"})

    # Count existing exercise attempts for this session
    attempt_count = db.query(ExerciseAttempt).filter(
        ExerciseAttempt.session_id == session_id
    ).count()

    # If all 8 attempts are done, return completion
    if attempt_count >= 8:
        return {
            "complete": True,
            "message": "Session complete"
        }

    # Determine which domain based on attempt count (0-3 -> domain_1, 4-7 -> domain_2)
    if attempt_count < 4:
        domain = session.domain_1
    else:
        domain = session.domain_2

    # Exercise types per domain
    domain_exercise_map = {
        "processing_speed": ["symbol_matching", "visual_categorisation"],
        "working_memory": ["n_back", "digit_span"],
        "attention": ["go_no_go", "stroop"]
    }

    exercises = domain_exercise_map.get(domain, [])
    if not exercises:
        raise HTTPException(status_code=400, detail={"message": f"Invalid domain: {domain}"})

    # Alternate exercise type within each domain
    # For each domain: attempts 0-1 -> first exercise, attempts 2-3 -> second exercise
    attempt_index_in_domain = attempt_count % 4
    exercise_type_index = attempt_index_in_domain // 2
    exercise_type = exercises[exercise_type_index] if exercise_type_index < len(exercises) else exercises[0]

    # Re-read current_difficulty from the DB to pick up any updates committed
    # during this session rather than using a session-start cached value.
    progress = db.query(DomainProgress).filter(
        DomainProgress.user_id == current_user.id,
        DomainProgress.domain == domain
    ).first()
    difficulty_level = progress.current_difficulty if progress else 1

    return {
        "exercise_type": exercise_type,
        "domain": domain,
        "difficulty_level": difficulty_level,
        "trials_to_complete": 8
    }

@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(DBSession).filter(DBSession.id == session_id).first()
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail={"message": "Session not found"})

    return SessionResponse.model_validate(session)

@router.get("")
def list_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    sessions = db.query(DBSession).filter(DBSession.user_id == current_user.id).all()
    return [SessionResponse.model_validate(s) for s in sessions]

@router.post("/plan-next")
def plan_next_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = SessionPlannerService.plan_session(db, current_user.id)
    return plan
