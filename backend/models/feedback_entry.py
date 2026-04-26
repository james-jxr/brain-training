from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base


class FeedbackEntry(Base):
    __tablename__ = "feedback_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    page_context = Column(String, nullable=False)  # max 100 chars in practice
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True)
    feedback_text = Column(String, nullable=False)  # max 1000 chars in practice
    project_id = Column(String, nullable=False, default="brain-training")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="feedback_entries")
    session = relationship("Session", back_populates="feedback_entries")
