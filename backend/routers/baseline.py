from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone, date
from typing import List
from backend.database import get_db
from backend.models import User, Session as DBSession, DomainProgress, BaselineResult
from backend.schemas import SessionResponse, DomainScoreInput, BaselineResultResponse
from backend.security import get_current_user

router = APIRouter(prefix="/api/baseline", tags=["baseline"])

@router.post("/start")
def start_baseline(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # BUG-14: check eligibility using User-level field, not session history
    if current_user.next_baseline_eligible_date:
        today = date.today()
        if today < current_user.next_baseline_eligible_date:
            raise HTTPException(
                status_code=400,
                detail={"message": f"Next baseline eligible on {current_user.next_baseline_eligible_date}"}
            )

    # Auto-increment baseline_number per user
    existing_count = db.query(DBSession).filter(
        DBSession.user_id == current_user.id,
        DBSession.is_baseline == 1
    ).count()
    baseline_number = existing_count + 1

    baseline_session = DBSession(
        user_id=current_user.id,
        domain_1="processing_speed",
        domain_2="working_memory",
        is_baseline=1,
        baseline_number=baseline_number
    )
    db.add(baseline_session)
    db.commit()
    db.refresh(baseline_session)

    return SessionResponse.model_validate(baseline_session)

@router.post("/submit")
def submit_baseline(
    domain_scores: List[DomainScoreInput],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate domains
    valid_domains = {"processing_speed", "working_memory", "attention"}
    for score_input in domain_scores:
        if score_input.domain not in valid_domains:
            raise HTTPException(
                status_code=400,
                detail={"message": f"Invalid domain: {score_input.domain}"}
            )

    # Count completed baselines by distinct baseline_number in BaselineResult.
    # This is the source of truth — counting Sessions would include the session
    # created by /baseline/start before /baseline/submit is called, giving off-by-one.
    completed_baseline_count = db.query(BaselineResult.baseline_number).filter(
        BaselineResult.user_id == current_user.id
    ).distinct().count()
    baseline_number = completed_baseline_count + 1
    is_original = completed_baseline_count == 0

    # Create BaselineResult record for each domain
    baseline_results = []
    for score_input in domain_scores:
        baseline_result = BaselineResult(
            user_id=current_user.id,
            domain=score_input.domain,
            score=score_input.score,
            baseline_number=baseline_number,
            is_original=is_original
        )
        db.add(baseline_result)
        baseline_results.append(baseline_result)

    # Initialize or retrieve DomainProgress for each domain
    for score_input in domain_scores:
        progress = db.query(DomainProgress).filter(
            DomainProgress.user_id == current_user.id,
            DomainProgress.domain == score_input.domain
        ).first()

        if not progress:
            progress = DomainProgress(
                user_id=current_user.id,
                domain=score_input.domain,
                current_difficulty=1,
                last_score=score_input.score
            )
            db.add(progress)
        else:
            progress.last_score = score_input.score

    # Set user.onboarding_completed to True and anchor next eligible date (BUG-14 / BUG-12)
    current_user.onboarding_completed = True
    current_user.has_completed_baseline = True
    current_user.next_baseline_eligible_date = (date.today() + timedelta(days=180))

    db.commit()

    for result in baseline_results:
        db.refresh(result)

    return {
        "message": "Baseline submitted successfully",
        "baseline_number": baseline_number,
        "is_original": is_original,
        "results": [BaselineResultResponse.model_validate(r) for r in baseline_results]
    }

@router.get("/next-eligible-date")
def get_next_baseline_date(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # BUG-14: use User-level field as the single source of truth
    today = date.today()
    if not current_user.next_baseline_eligible_date:
        return {"next_eligible_date": today, "is_eligible": True}

    return {
        "next_eligible_date": current_user.next_baseline_eligible_date,
        "is_eligible": today >= current_user.next_baseline_eligible_date
    }
