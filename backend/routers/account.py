from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from typing import Optional
from backend.database import get_db
from backend.models import User
from backend.schemas import UserResponse
from backend.security import get_current_user, hash_password

router = APIRouter(prefix="/api/account", tags=["account"])

class AccountUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    notification_time: Optional[str] = None

    @field_validator('password')
    @classmethod
    def password_min_length(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

@router.get("/profile", response_model=UserResponse)
def get_profile(
    current_user: User = Depends(get_current_user)
):
    return UserResponse.model_validate(current_user)

@router.post("/onboarding-complete")
def mark_onboarding_complete(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    current_user.onboarding_completed = True
    db.commit()
    db.refresh(current_user)

    return {
        "message": "Onboarding completed",
        "user": UserResponse.model_validate(current_user)
    }

@router.get("/onboarding-status")
def get_onboarding_status(
    current_user: User = Depends(get_current_user)
):
    return {
        "onboarding_completed": current_user.onboarding_completed
    }

@router.patch("")
def update_account(
    update_data: AccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if update_data.email is not None:
        existing_email = db.query(User).filter(User.email == update_data.email).first()
        if existing_email and existing_email.id != current_user.id:
            raise HTTPException(status_code=400, detail={"message": "Email already in use"})
        current_user.email = update_data.email

    if update_data.password is not None:
        current_user.hashed_password = hash_password(update_data.password)

    if update_data.notification_time is not None:
        current_user.notification_time = update_data.notification_time

    db.commit()
    db.refresh(current_user)

    return UserResponse.model_validate(current_user)

@router.delete("")
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    response: Response = None
):
    db.delete(current_user)
    db.commit()

    response.delete_cookie("access_token")

    return {"message": "Account deleted successfully"}
