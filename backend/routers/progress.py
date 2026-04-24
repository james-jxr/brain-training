from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from backend.database import get_db
from backend.models import User, DomainProgress, ExerciseAttempt, Session as DBSession, LifestyleLog
from backend.schemas import DomainProgressResponse, ProgressSummary
from backend.security import get_current_user
from backend.services import BrainHealthScoreService, StreakManagerService, AdaptiveDifficultyService
from datetime import datetime, timedelta, date, timezone
from sqlalchemy import func

router = APIRouter(prefix="/api/progress", tags=["progress"])

@router.get("/domain/{domain}", response_model=DomainProgressResponse)
def get_domain_progress(
    domain: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    progress = db.query(DomainProgress).filter(
        and_(
            DomainProgress.user_id == current_user.id,
            DomainProgress.domain == domain
        )
    ).first()

    if not progress:
        raise HTTPException(status_code=404, detail={"message": "Domain progress not found"})

    return DomainProgressResponse.model_validate(progress)

@router.get("/summary")
def get_progress_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    domains = ["processing_speed", "working_memory", "attention"]
    summary_data = []

    for domain in domains:
        progress = db.query(DomainProgress).filter(
            and_(
                DomainProgress.user_id == current_user.id,
                DomainProgress.domain == domain
            )
        ).first()

        difficulty = progress.current_difficulty if progress else 1
        last_score = progress.last_score if progress else None
        total_attempts = progress.total_attempts if progress else 0
        total_correct = progress.total_correct if progress else 0

        average_score = (total_correct / total_attempts * 100) if total_attempts > 0 else 0

        summary_data.append({
            "domain": domain,
            "current_difficulty": difficulty,
            "last_score": last_score,
            "total_sessions": 0,
            "average_score": average_score,
            "brain_health_score": 0,
            "streak": StreakManagerService.get_current_streak(db, current_user.id),
            "longest_streak": StreakManagerService.get_longest_streak(db, current_user.id)
        })

    brain_health = BrainHealthScoreService.calculate_brain_health_score(db, current_user.id)

    return {
        "domains": summary_data,
        "brain_health_score": brain_health
    }

@router.get("/brain-health")
def get_brain_health_score(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    score = BrainHealthScoreService.calculate_brain_health_score(db, current_user.id)
    domain_avg = BrainHealthScoreService.calculate_domain_average(db, current_user.id)
    lifestyle_score = BrainHealthScoreService.calculate_lifestyle_score(db, current_user.id)

    return {
        "brain_health_score": score,
        "domain_average": domain_avg,
        "lifestyle_score": lifestyle_score
    }

@router.get("/streak")
def get_streak(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current = StreakManagerService.get_current_streak(db, current_user.id)
    longest = StreakManagerService.get_longest_streak(db, current_user.id)

    return {
        "current_streak": current,
        "longest_streak": longest
    }

@router.get("/streak/history")
def get_streak_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_streak = StreakManagerService.get_current_streak(db, current_user.id)
    longest_streak = StreakManagerService.get_longest_streak(db, current_user.id)

    today = date.today()
    start_date = today - timedelta(days=13)

    completed_sessions = db.query(
        func.date(DBSession.completed_at).label("session_date")
    ).filter(
        DBSession.user_id == current_user.id,
        DBSession.completed_at.isnot(None),
        func.date(DBSession.completed_at) >= start_date,
        func.date(DBSession.completed_at) <= today
    ).distinct().all()

    active_dates = set()
    for row in completed_sessions:
        session_date = row.session_date
        if isinstance(session_date, str):
            session_date = date.fromisoformat(session_date)
        active_dates.add(session_date)

    days = []
    for i in range(14):
        current_date = start_date + timedelta(days=i)
        days.append({
            "date": current_date.isoformat(),
            "completed": current_date in active_dates,
            "is_today": current_date == today
        })

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "days": days
    }

@router.get("/dashboard")
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get streak information
    current_streak = StreakManagerService.get_current_streak(db, current_user.id)
    longest_streak = StreakManagerService.get_longest_streak(db, current_user.id)

    # Calculate total training seconds
    # For now, count completed sessions * 900 (15 min average) as duration is not stored
    completed_sessions = db.query(DBSession).filter(
        DBSession.user_id == current_user.id,
        DBSession.completed_at.isnot(None)
    ).count()
    total_training_seconds = completed_sessions * 900

    # Get brain health score
    brain_health_score = BrainHealthScoreService.calculate_brain_health_score(db, current_user.id)

    # Get domain scores
    domains = ["processing_speed", "working_memory", "attention"]
    domain_scores = []
    for domain in domains:
        progress = db.query(DomainProgress).filter(
            DomainProgress.user_id == current_user.id,
            DomainProgress.domain == domain
        ).first()

        if progress:
            domain_scores.append({
                "domain": domain,
                "score": progress.last_score if progress.last_score is not None else 0,
                "difficulty": progress.current_difficulty
            })

    # Get lifestyle summary (today's data)
    today = date.today()
    lifestyle_log = db.query(LifestyleLog).filter(
        LifestyleLog.user_id == current_user.id,
        LifestyleLog.logged_date == today
    ).first()

    if lifestyle_log:
        lifestyle_summary = {
            "exercise_minutes": lifestyle_log.exercise_minutes,
            "sleep_hours": lifestyle_log.sleep_hours,
            "stress_level": lifestyle_log.stress_level,
            "mood": lifestyle_log.mood
        }
    else:
        lifestyle_summary = {
            "exercise_minutes": 0.0,
            "sleep_hours": 0.0,
            "stress_level": 5,
            "mood": 5
        }

    return {
        "streak": {
            "current": current_streak,
            "longest": longest_streak
        },
        "total_training_seconds": total_training_seconds,
        "brain_health_score": brain_health_score,
        "domain_scores": domain_scores,
        "lifestyle_summary": lifestyle_summary
    }

@router.get("/trend/{domain}")
def get_domain_trend(
    domain: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

    attempts = db.query(ExerciseAttempt).join(
        DBSession, ExerciseAttempt.session_id == DBSession.id
    ).filter(
        and_(
            DBSession.user_id == current_user.id,
            ExerciseAttempt.domain == domain,
            DBSession.started_at >= thirty_days_ago
        )
    ).all()

    trend_data = []
    for attempt in attempts:
        score = (attempt.trials_correct / attempt.trials_presented * 100) if attempt.trials_presented > 0 else 0
        trend_data.append({
            "date": attempt.session.started_at,
            "score": score,
            "difficulty": attempt.difficulty  # BUG-19: return actual difficulty, not hardcoded 0
        })

    return {
        "domain": domain,
        "data": trend_data
    }

@router.get("/game-history")
def get_game_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    exercise_types = db.query(ExerciseAttempt.exercise_type).join(
        DBSession, ExerciseAttempt.session_id == DBSession.id
    ).filter(
        DBSession.user_id == current_user.id,
        ExerciseAttempt.exercise_type.isnot(None)
    ).distinct().all()

    game_data = {}
    for (exercise_type,) in exercise_types:
        attempts = db.query(ExerciseAttempt).join(
            DBSession, ExerciseAttempt.session_id == DBSession.id
        ).filter(
            DBSession.user_id == current_user.id,
            ExerciseAttempt.exercise_type == exercise_type
        ).order_by(
            ExerciseAttempt.completed_at.desc()
        ).limit(20).all()

        attempts_reversed = list(reversed(attempts))

        entries = []
        for attempt in attempts_reversed:
            if attempt.trials_presented and attempt.trials_presented > 0:
                score = attempt.trials_correct / attempt.trials_presented * 100
            elif attempt.score is not None:
                score = float(attempt.score)
            else:
                score = 0.0

            attempt_date = attempt.completed_at
            if attempt_date is None and attempt.session is not None:
                attempt_date = attempt.session.started_at

            entries.append({
                "date": attempt_date.isoformat() if attempt_date else None,
                "score": round(score, 1),
                "difficulty": attempt.difficulty
            })

        game_data[exercise_type] = entries

    return {
        "games": game_data
    }
