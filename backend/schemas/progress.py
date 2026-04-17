from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DomainProgressResponse(BaseModel):
    id: int
    user_id: int
    domain: str
    current_difficulty: int
    consecutive_correct: int
    consecutive_incorrect: int
    last_score: Optional[float]
    total_attempts: int
    total_correct: int
    updated_at: datetime

    class Config:
        from_attributes = True

class ProgressSummary(BaseModel):
    domain: str
    current_difficulty: int
    last_score: Optional[float]
    total_sessions: int
    average_score: float
    brain_health_score: int
    streak: int
    longest_streak: int
