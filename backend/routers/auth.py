from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User
from backend.schemas import UserLogin, UserRegister, TokenResponse, UserResponse
from backend.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from datetime import timedelta, datetime, timezone

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_auth_cookie(response: Response, access_token: str):
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=86400,
        path="/",
    )


@router.post("/register", response_model=TokenResponse)
def register(user_data: UserRegister, response: Response, db: Session = Depends(get_db)):
    if not user_data.consent_given:
        raise HTTPException(status_code=400, detail={"message": "You must accept the terms to register"})

    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail={"message": "Email already registered"})

    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail={"message": "Username already taken"})

    hashed_pw = hash_password(user_data.password)
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_pw,
        consent_given_at=datetime.now(timezone.utc)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(days=1)
    )

    _set_auth_cookie(response, access_token)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail={"message": "Invalid credentials"})

    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(days=1)
    )

    _set_auth_cookie(response, access_token)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token", path="/", secure=True, samesite="none")
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
