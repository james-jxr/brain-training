# Tracks each run of the autonomous feedback agent pipeline.
from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime, timezone
from backend.database import Base


class FeedbackRun(Base):
    __tablename__ = "feedback_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    feedback_count = Column(Integer, default=0)       # items processed in this run
    themes = Column(JSON, nullable=True)               # synthesised theme list
    changes_applied = Column(JSON, nullable=True)      # list of change dicts
    branch_name = Column(String, nullable=True)        # git branch created
    pr_url = Column(String, nullable=True)             # GitHub PR URL
    status = Column(String, default='pending')         # pending | completed | failed | no_changes
    error = Column(String, nullable=True)              # error message if status=failed
