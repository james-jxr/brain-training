from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class DomainProgress(Base):
    __tablename__ = "domain_progress"
    __table_args__ = (UniqueConstraint('user_id', 'domain', name='unique_user_domain'),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    domain = Column(String)
    current_difficulty = Column(Integer, default=1)
    consecutive_correct = Column(Integer, default=0)
    consecutive_incorrect = Column(Integer, default=0)
    last_score = Column(Float, nullable=True)
    total_attempts = Column(Integer, default=0)
    total_correct = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="domain_progress")
