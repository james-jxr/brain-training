from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.database import Base


class SkillAssessment(Base):
    __tablename__ = "skill_assessments"
    __table_args__ = (
        UniqueConstraint("user_id", "game_key", name="uq_skill_assessment_user_game"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # Canonical game keys: nback, card_memory, digit_span, go_no_go,
    #                      stroop, symbol_matching, visual_categorisation
    game_key = Column(String, nullable=False)
    # 1 = Easy, 2 = Medium, 3 = Hard
    assessed_level = Column(Integer, nullable=False, default=1)
    assessed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    baseline_count = Column(Integer, nullable=False, default=1)

    user = relationship("User", back_populates="skill_assessments")
