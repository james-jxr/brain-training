from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from backend.database import get_db, settings
from backend.models import User, FeedbackEntry
from backend.schemas import FeedbackCreate, FeedbackResponse, FeedbackEntryGroup, FeedbackExportResponse
from backend.security import get_current_user, get_current_user_optional

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

PROJECT_ID = "brain-training"


def _require_admin(current_user: User) -> None:
    """Raise 403 if the current user is not in the ADMIN_EMAILS list."""
    admin_emails = {e.strip() for e in settings.ADMIN_EMAILS.split(",") if e.strip()}
    if not admin_emails:
        raise HTTPException(status_code=403, detail="Admin access not configured")
    if current_user.email not in admin_emails:
        raise HTTPException(status_code=403, detail="Admin access required")


@router.post("", response_model=FeedbackResponse)
def submit_feedback(
    feedback_data: FeedbackCreate,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Submit free-text feedback from an authenticated user."""
    # Validate page_context length
    if len(feedback_data.page_context) > 100:
        raise HTTPException(status_code=400, detail="page_context must be max 100 chars")

    # Validate feedback_text length
    if len(feedback_data.feedback_text) > 1000:
        raise HTTPException(status_code=400, detail="feedback_text must be max 1000 chars")

    if len(feedback_data.feedback_text.strip()) == 0:
        raise HTTPException(status_code=400, detail="feedback_text cannot be empty")

    feedback = FeedbackEntry(
        user_id=current_user.id if current_user else None,
        page_context=feedback_data.page_context,
        session_id=feedback_data.session_id,
        feedback_text=feedback_data.feedback_text,
        project_id=PROJECT_ID,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return FeedbackResponse.model_validate(feedback)


@router.get("", response_model=FeedbackExportResponse)
def export_feedback(
    from_date: str = None,
    to_date: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export all feedback entries grouped by page_context. Admin only.

    Query params:
    - from_date: ISO date string (e.g. "2026-04-01"), optional
    - to_date: ISO date string (e.g. "2026-04-30"), optional
    """
    _require_admin(current_user)

    query = db.query(FeedbackEntry)

    # Apply date filters if provided
    if from_date:
        try:
            from_dt = datetime.fromisoformat(from_date)
            query = query.filter(FeedbackEntry.created_at >= from_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="from_date must be ISO format")

    if to_date:
        try:
            to_dt = datetime.fromisoformat(to_date)
            # Include entire day by going to next day at 00:00
            to_dt = to_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(FeedbackEntry.created_at <= to_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="to_date must be ISO format")

    entries = query.order_by(FeedbackEntry.created_at.desc()).all()

    # Group by page_context
    groups_dict = {}
    for entry in entries:
        context = entry.page_context
        if context not in groups_dict:
            groups_dict[context] = []
        groups_dict[context].append(FeedbackResponse.model_validate(entry))

    groups = [
        FeedbackEntryGroup(page_context=context, entries=feedback_list)
        for context, feedback_list in sorted(groups_dict.items())
    ]

    return FeedbackExportResponse(total=len(entries), groups=groups)
