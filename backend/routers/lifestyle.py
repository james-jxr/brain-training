from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date, datetime, timedelta
from backend.database import get_db
from backend.models import User, LifestyleLog
from backend.schemas import LifestyleLogCreate, LifestyleLogResponse
from backend.security import get_current_user

router = APIRouter(prefix="/api/lifestyle", tags=["lifestyle"])

@router.post("/log", response_model=LifestyleLogResponse)
def log_lifestyle(
    lifestyle_data: LifestyleLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    today = date.today()

    existing = db.query(LifestyleLog).filter(
        and_(
            LifestyleLog.user_id == current_user.id,
            LifestyleLog.logged_date == today
        )
    ).first()

    if existing:
        existing.exercise_minutes = lifestyle_data.exercise_minutes
        existing.sleep_hours = lifestyle_data.sleep_hours
        existing.stress_level = lifestyle_data.stress_level
        existing.mood = lifestyle_data.mood
        existing.sleep_quality = lifestyle_data.sleep_quality
        existing.social_engagement = lifestyle_data.social_engagement
        db.commit()
        db.refresh(existing)
        return LifestyleLogResponse.model_validate(existing)

    log = LifestyleLog(
        user_id=current_user.id,
        logged_date=today,
        exercise_minutes=lifestyle_data.exercise_minutes,
        sleep_hours=lifestyle_data.sleep_hours,
        stress_level=lifestyle_data.stress_level,
        mood=lifestyle_data.mood,
        sleep_quality=lifestyle_data.sleep_quality,
        social_engagement=lifestyle_data.social_engagement
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return LifestyleLogResponse.model_validate(log)

@router.get("/today", response_model=LifestyleLogResponse)
def get_today_lifestyle(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    today = date.today()

    log = db.query(LifestyleLog).filter(
        and_(
            LifestyleLog.user_id == current_user.id,
            LifestyleLog.logged_date == today
        )
    ).first()

    if not log:
        raise HTTPException(status_code=404, detail={"message": "No lifestyle log for today"})

    return LifestyleLogResponse.model_validate(log)

@router.get("/history")
def get_lifestyle_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    logs = db.query(LifestyleLog).filter(
        and_(
            LifestyleLog.user_id == current_user.id,
            LifestyleLog.created_at >= thirty_days_ago
        )
    ).order_by(LifestyleLog.logged_date.desc()).all()

    return [LifestyleLogResponse.model_validate(log) for log in logs]
