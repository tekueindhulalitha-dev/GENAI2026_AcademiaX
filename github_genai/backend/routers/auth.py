# backend/routers/auth.py
"""
Authentication endpoints matching the Streamlit login page.

POST /auth/register  – create new account
POST /auth/login     – returns JWT token
GET  /auth/me        – returns current user profile + stats
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.database import User, get_db
from models.schemas  import Token, UserCreate, UserLogin, UserOut
from utils.security  import (
    create_access_token, get_current_user, hash_password, verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Register ─────────────────────────────────────────────────
@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new researcher account.
    Returns 409 if email already exists.
    """
    if db.query(User).filter_by(email=user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email           = user_data.email,
        hashed_password = hash_password(user_data.password),
        full_name       = user_data.full_name,
        plan            = "free",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── Login ─────────────────────────────────────────────────────
@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Validate credentials and return a JWT bearer token.
    The Streamlit app stores this token and sends it with every API call.
    """
    user = db.query(User).filter_by(email=credentials.email).first()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled. Please contact support.",
        )

    return Token(access_token=create_access_token(user.id))


# ── Current user profile ──────────────────────────────────────
@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the profile of the currently authenticated user."""
    return current_user


# ── Update profile ────────────────────────────────────────────
@router.patch("/me", response_model=UserOut)
def update_me(
    updates: dict,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Update full_name or password."""
    if "full_name" in updates:
        current_user.full_name = updates["full_name"]

    if "password" in updates:
        current_user.hashed_password = hash_password(updates["password"])

    db.commit()
    db.refresh(current_user)
    return current_user
