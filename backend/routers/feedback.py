from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from backend.database import get_db
from backend.models import User, FeedbackEntry
from backend.schemas import FeedbackCreate, FeedbackResponse, FeedbackEntryGroup, FeedbackExportResponse
from backend.security import get_current_user, get_current_user_optional

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


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
    """Export all feedback entries grouped by page_context.

    Query params:
    - from_date: ISO date string (e.g. "2026-04-01"), optional
    - to_date: ISO date string (e.g. "2026-04-30"), optional

    Intended for pipeline use to feed the Feedback Synthesis step.
    Returns all feedback (across all users) if called by any authenticated user.
    """
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
