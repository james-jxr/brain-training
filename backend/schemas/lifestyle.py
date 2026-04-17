from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class LifestyleLogCreate(BaseModel):
    exercise_minutes: float
    sleep_hours: float
    stress_level: int
    mood: int
    sleep_quality: Optional[int] = None
    social_engagement: Optional[int] = None

class LifestyleLogResponse(BaseModel):
    id: int
    user_id: int
    logged_date: date
    exercise_minutes: float
    sleep_hours: float
    stress_level: int
    mood: int
    sleep_quality: Optional[int] = None
    social_engagement: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
