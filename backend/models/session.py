from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    domain_1 = Column(String)
    domain_2 = Column(String)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    is_baseline = Column(Integer, default=0)
    baseline_number = Column(Integer, nullable=True)

    user = relationship("User", back_populates="sessions")
    exercise_attempts = relationship("ExerciseAttempt", back_populates="session", cascade="all, delete-orphan")
    feedback_entries = relationship("FeedbackEntry", back_populates="session", cascade="all, delete-orphan")
