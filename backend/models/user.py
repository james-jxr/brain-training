from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base

def _now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)
    is_active = Column(Boolean, default=True)
    onboarding_completed = Column(Boolean, default=False)
    has_completed_baseline = Column(Boolean, default=False)
    notification_time = Column(String, nullable=True)
    # BUG-08: GDPR consent timestamp
    consent_given_at = Column(DateTime, nullable=True)
    # BUG-12: cumulative training time and baseline eligibility anchor
    total_training_seconds = Column(Integer, default=0)
    next_baseline_eligible_date = Column(Date, nullable=True)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    domain_progress = relationship("DomainProgress", back_populates="user", cascade="all, delete-orphan")
    lifestyle_logs = relationship("LifestyleLog", back_populates="user", cascade="all, delete-orphan")
    streak = relationship("Streak", back_populates="user", uselist=False, cascade="all, delete-orphan")
    baseline_results = relationship("BaselineResult", back_populates="user", cascade="all, delete-orphan")
    feedback_entries = relationship("FeedbackEntry", back_populates="user", cascade="all, delete-orphan")
    skill_assessments = relationship("SkillAssessment", back_populates="user", cascade="all, delete-orphan")
