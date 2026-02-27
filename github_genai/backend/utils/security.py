# backend/utils/security.py
"""
JWT token creation / verification + bcrypt password hashing.
Used by every protected endpoint via Depends(get_current_user).
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from models.database import User, get_db
from models.schemas  import TokenData

load_dotenv()

SECRET_KEY  = os.getenv("SECRET_KEY",  "change_this_secret_in_production")
ALGORITHM   = os.getenv("ALGORITHM",   "HS256")
TOKEN_EXPIRE = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 h

pwd_context      = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme    = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ── Password helpers ──────────────────────────────────────────
def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT helpers ───────────────────────────────────────────────
def create_access_token(user_id: int) -> str:
    expire  = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Optional[TokenData]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        return TokenData(user_id=user_id)
    except (JWTError, TypeError, ValueError):
        return None


# ── FastAPI dependency ────────────────────────────────────────
def get_current_user(
    token: str      = Depends(oauth2_scheme),
    db:    Session  = Depends(get_db),
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = decode_token(token)
    if not token_data:
        raise credentials_exc

    user = db.query(User).filter(User.id == token_data.user_id, User.is_active == True).first()
    if not user:
        raise credentials_exc
    return user
