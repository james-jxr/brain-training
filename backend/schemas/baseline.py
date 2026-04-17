from pydantic import BaseModel
from datetime import datetime
from typing import List

class DomainScoreInput(BaseModel):
    domain: str
    score: float

class BaselineResultResponse(BaseModel):
    id: int
    user_id: int
    domain: str
    score: float
    baseline_number: int
    is_original: bool
    completed_at: datetime

    class Config:
        from_attributes = True
