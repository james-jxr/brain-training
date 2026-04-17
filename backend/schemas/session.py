from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ExerciseAttemptCreate(BaseModel):
    domain: str
    exercise_type: str
    trials_presented: Optional[int] = None
    trials_correct: Optional[int] = None
    avg_response_ms: Optional[float] = None
    difficulty: Optional[str] = None
    card_count: Optional[int] = None
    correct: Optional[bool] = None
    response_time_ms: Optional[int] = None
    score: Optional[int] = None

class ExerciseAttemptResponse(BaseModel):
    id: int
    session_id: int
    domain: str
    exercise_type: str
    trials_presented: Optional[int] = None
    trials_correct: Optional[int] = None
    avg_response_ms: Optional[float] = None
    difficulty: Optional[str] = None
    card_count: Optional[int] = None
    correct: Optional[bool] = None
    response_time_ms: Optional[int] = None
    score: Optional[int] = None
    completed_at: datetime

    class Config:
        from_attributes = True

class SessionCreate(BaseModel):
    domain_1: str
    domain_2: str
    is_baseline: int = 0

class SessionResponse(BaseModel):
    id: int
    user_id: int
    domain_1: str
    domain_2: str
    started_at: datetime
    completed_at: Optional[datetime]
    is_baseline: int
    baseline_number: Optional[int]
    exercise_attempts: List[ExerciseAttemptResponse] = []

    class Config:
        from_attributes = True
