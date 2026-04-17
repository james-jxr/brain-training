from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base

class ExerciseAttempt(Base):
    __tablename__ = "exercise_attempts"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), index=True)
    domain = Column(String)
    exercise_type = Column(String)
    trials_presented = Column(Integer, nullable=True)
    trials_correct = Column(Integer, nullable=True)
    avg_response_ms = Column(Float, nullable=True)
    difficulty = Column(String, nullable=True)
    card_count = Column(Integer, nullable=True)
    correct = Column(Boolean, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    score = Column(Integer, nullable=True)
    completed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    session = relationship("Session", back_populates="exercise_attempts")
