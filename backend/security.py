from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, Cookie, Request
from sqlalchemy.orm import Session
from backend.database import get_db, settings
from backend.models import User
from typing import Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=1)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def get_current_user(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> User:
    # Accept JWT from Authorization: Bearer header (API clients / tests) first,
    # then fall back to the httpOnly cookie (browser).
    # Prioritising the explicit header means a caller that sets both (e.g. TestClient
    # with a stale cookie jar) is authenticated as the user they actually intend.
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header[7:]
    else:
        token = access_token
    if not token:
        raise HTTPException(status_code=401, detail={"message": "Not authenticated"})

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise HTTPException(status_code=401, detail={"message": "Invalid token"})
        user_id: int = int(sub)  # raises ValueError if sub is not numeric
    except (JWTError, ValueError):
        # BUG-20: catch ValueError from int(sub) — previously unreachable branch removed
        raise HTTPException(status_code=401, detail={"message": "Invalid token"})

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail={"message": "User not found"})

    return user

def get_current_user_optional(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    try:
        return get_current_user(request, access_token, db)
    except HTTPException:
        return None
