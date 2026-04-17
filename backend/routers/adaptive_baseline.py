from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from backend.database import get_db
from backend.models import User
from backend.models.skill_assessment import SkillAssessment
from backend.models.domain_progress import DomainProgress
from backend.schemas.adaptive_baseline import (
    CompleteBaselineRequest,
    AdaptiveBaselineStatusResponse,
    CompleteBaselineResponse,
    SkillAssessmentResponse,
    GAME_DISPLAY_NAMES,
    DIFFICULTY_LABELS,
)
from backend.security import get_current_user

router = APIRouter(prefix="/api/adaptive-baseline", tags=["adaptive-baseline"])


def _assessment_to_response(assessment: SkillAssessment) -> SkillAssessmentResponse:
    """Convert a SkillAssessment ORM object to the API response shape."""
    return SkillAssessmentResponse(
        game_key=assessment.game_key,
        game_name=GAME_DISPLAY_NAMES.get(assessment.game_key, assessment.game_key),
        assessed_level=assessment.assessed_level,
        difficulty_label=DIFFICULTY_LABELS.get(assessment.assessed_level, "Unknown"),
        assessed_at=assessment.assessed_at,
        baseline_count=assessment.baseline_count,
    )


@router.get("/status", response_model=AdaptiveBaselineStatusResponse)
def get_adaptive_baseline_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return whether the current user has completed the adaptive baseline test
    and their full current skill profile.
    """
    assessments = (
        db.query(SkillAssessment)
        .filter(SkillAssessment.user_id == current_user.id)
        .order_by(SkillAssessment.game_key)
        .all()
    )

    profile = [_assessment_to_response(a) for a in assessments]

    return AdaptiveBaselineStatusResponse(
        has_completed=current_user.has_completed_baseline,
        profile=profile,
    )


@router.post("/complete", response_model=CompleteBaselineResponse)
def complete_adaptive_baseline(
    payload: CompleteBaselineRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit the results of a completed adaptive baseline test.

    Upserts one SkillAssessment row per game (last result wins), increments
    baseline_count, and sets user.has_completed_baseline = True.
    """
    if not payload.results:
        raise HTTPException(
            status_code=400,
            detail={"message": "results list must not be empty"},
        )

    # Validate there are no duplicate game_keys in the submission
    submitted_keys = [r.game_key for r in payload.results]
    if len(submitted_keys) != len(set(submitted_keys)):
        raise HTTPException(
            status_code=400,
            detail={"message": "Duplicate game_key entries in results"},
        )

    updated_assessments = []

    for result in payload.results:
        existing = (
            db.query(SkillAssessment)
            .filter(
                SkillAssessment.user_id == current_user.id,
                SkillAssessment.game_key == result.game_key,
            )
            .first()
        )

        if existing:
            existing.assessed_level = result.assessed_level
            existing.assessed_at = datetime.utcnow()
            existing.baseline_count += 1
            updated_assessments.append(existing)
        else:
            new_assessment = SkillAssessment(
                user_id=current_user.id,
                game_key=result.game_key,
                assessed_level=result.assessed_level,
                assessed_at=datetime.utcnow(),
                baseline_count=1,
            )
            db.add(new_assessment)
            updated_assessments.append(new_assessment)

    current_user.has_completed_baseline = True

    # Seed DomainProgress from baseline results so BrainHealthScore is non-zero
    GAME_DOMAIN_MAP = {
        "stroop": "processing_speed",
        "go_no_go": "processing_speed",
        "symbol_matching": "processing_speed",
        "nback": "working_memory",
        "digit_span": "working_memory",
        "card_memory": "working_memory",
        "visual_categorisation": "attention",
    }
    domain_levels: dict[str, list[int]] = {}
    for result in payload.results:
        domain = GAME_DOMAIN_MAP.get(result.game_key)
        if domain:
            domain_levels.setdefault(domain, []).append(result.assessed_level)

    for domain, levels in domain_levels.items():
        avg_level = sum(levels) / len(levels)
        seeded_score = (avg_level / 3.0) * 100.0
        seeded_difficulty = max(1, round(avg_level))

        existing = db.query(DomainProgress).filter(
            DomainProgress.user_id == current_user.id,
            DomainProgress.domain == domain,
        ).first()

        if existing:
            # Only update if no real training data yet
            if existing.total_attempts == 0:
                existing.last_score = seeded_score
                existing.current_difficulty = seeded_difficulty
        else:
            db.add(DomainProgress(
                user_id=current_user.id,
                domain=domain,
                current_difficulty=seeded_difficulty,
                last_score=seeded_score,
            ))

    db.commit()

    # Refresh all updated/inserted rows to get final state
    for assessment in updated_assessments:
        db.refresh(assessment)

    profile = [_assessment_to_response(a) for a in updated_assessments]
    profile.sort(key=lambda x: x.game_key)

    return CompleteBaselineResponse(
        message="Baseline assessment saved successfully",
        profile=profile,
    )
