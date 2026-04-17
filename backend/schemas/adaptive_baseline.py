from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import List

# Canonical game keys accepted by the API
VALID_GAME_KEYS = {
    "nback",
    "card_memory",
    "digit_span",
    "go_no_go",
    "stroop",
    "symbol_matching",
    "visual_categorisation",
}

GAME_DISPLAY_NAMES = {
    "nback": "Count Back Match",
    "card_memory": "Card Memory",
    "digit_span": "Digit Span",
    "go_no_go": "Go / No-Go",
    "stroop": "Stroop",
    "symbol_matching": "Symbol Matching",
    "visual_categorisation": "Visual Categorisation",
}

DIFFICULTY_LABELS = {1: "Easy", 2: "Medium", 3: "Hard"}


class GameResultInput(BaseModel):
    game_key: str
    assessed_level: int  # 1, 2, or 3

    @field_validator("game_key")
    @classmethod
    def validate_game_key(cls, v: str) -> str:
        if v not in VALID_GAME_KEYS:
            raise ValueError(f"Invalid game_key '{v}'. Must be one of: {sorted(VALID_GAME_KEYS)}")
        return v

    @field_validator("assessed_level")
    @classmethod
    def validate_assessed_level(cls, v: int) -> int:
        if v not in (1, 2, 3):
            raise ValueError("assessed_level must be 1 (Easy), 2 (Medium), or 3 (Hard)")
        return v


class CompleteBaselineRequest(BaseModel):
    results: List[GameResultInput]


class SkillAssessmentResponse(BaseModel):
    game_key: str
    game_name: str
    assessed_level: int
    difficulty_label: str
    assessed_at: datetime
    baseline_count: int

    class Config:
        from_attributes = True


class AdaptiveBaselineStatusResponse(BaseModel):
    has_completed: bool
    profile: List[SkillAssessmentResponse]


class CompleteBaselineResponse(BaseModel):
    message: str
    profile: List[SkillAssessmentResponse]
