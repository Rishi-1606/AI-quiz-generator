from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/profile", tags=["Profile"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class ProfileResponse(BaseModel):
    id:          int
    name:        str
    email:       str
    role:        str
    bio:         Optional[str]
    daily_goal:  int
    created_at:  datetime

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    name:       Optional[str]   = None
    bio:        Optional[str]   = None
    daily_goal: Optional[int]   = None   # 1–10 quizzes/day


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("", response_model=ProfileResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    """Return the current user's profile."""
    return current_user


@router.patch("", response_model=ProfileResponse)
def update_profile(
    body: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update name, bio, or daily goal."""
    if body.name is not None:
        if not body.name.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Name cannot be empty.")
        current_user.name = body.name.strip()

    if body.bio is not None:
        current_user.bio = body.bio.strip() or None

    if body.daily_goal is not None:
        if not (1 <= body.daily_goal <= 10):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Daily goal must be between 1 and 10.")
        current_user.daily_goal = body.daily_goal

    db.commit()
    db.refresh(current_user)
    return current_user
