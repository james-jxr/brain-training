from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FeedbackCreate(BaseModel):
    page_context: str
    feedback_text: str
    session_id: Optional[int] = None


class FeedbackResponse(BaseModel):
    id: int
    user_id: Optional[int]
    page_context: str
    session_id: Optional[int]
    feedback_text: str
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackEntryGroup(BaseModel):
    page_context: str
    entries: list[FeedbackResponse]


class FeedbackExportResponse(BaseModel):
    total: int
    groups: list[FeedbackEntryGroup]
