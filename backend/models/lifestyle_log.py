from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Date, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, date, timezone
from backend.database import Base

class LifestyleLog(Base):
    __tablename__ = "lifestyle_logs"
    __table_args__ = (UniqueConstraint('user_id', 'logged_date', name='unique_user_logged_date'),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    logged_date = Column(Date, default=date.today)
    exercise_minutes = Column(Float, default=0)
    sleep_hours = Column(Float, default=0)
    stress_level = Column(Integer, default=5)
    mood = Column(Integer, default=5)
    sleep_quality = Column(Integer, nullable=True)   # 1-5
    social_engagement = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="lifestyle_logs")
