from pydantic import BaseModel, EmailStr
from typing import Optional

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    consent_given: bool = False  # BUG-08: GDPR consent must be true to register

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    onboarding_completed: bool

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
