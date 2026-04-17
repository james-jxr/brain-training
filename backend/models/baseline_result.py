from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class BaselineResult(Base):
    __tablename__ = "baseline_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    domain = Column(String)  # processing_speed, working_memory, attention
    score = Column(Float)    # 0.0-100.0
    baseline_number = Column(Integer)  # 1=original, 2=first re-baseline, etc.
    is_original = Column(Boolean, default=False)
    completed_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="baseline_results")
