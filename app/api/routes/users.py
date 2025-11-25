# app/api/routes/users.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.db import models
from app.schemas.user import (
    UserOut,
    UserProfileOut,
    UserProfileBase,
    UserSchoolAnchorOut,
    UserSchoolAnchorCreate,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def get_me(
    current_user: models.User = Depends(get_current_user),
):
    return current_user


@router.get("/me/profile", response_model=UserProfileOut)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    profile = (
        db.execute(
            select(models.UserProfile).where(models.UserProfile.user_id == current_user.id)
        )
        .scalars()
        .first()
    )
    if not profile:
        profile = models.UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.put("/me/profile", response_model=UserProfileOut)
def update_my_profile(
    payload: UserProfileBase,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    profile = (
        db.execute(
            select(models.UserProfile).where(models.UserProfile.user_id == current_user.id)
        )
        .scalars()
        .first()
    )
    if not profile:
        profile = models.UserProfile(user_id=current_user.id)
        db.add(profile)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


@router.get("/me/school-anchors", response_model=list[UserSchoolAnchorOut])
def list_my_school_anchors(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    anchors = (
        db.execute(
            select(models.UserSchoolAnchor)
            .where(
                models.UserSchoolAnchor.user_id == current_user.id,
                models.UserSchoolAnchor.is_deleted == False,
            )
            .order_by(models.UserSchoolAnchor.created_at.desc())
        )
        .scalars()
        .all()
    )
    return anchors


@router.post("/me/school-anchors", response_model=UserSchoolAnchorOut)
def create_my_school_anchor(
    payload: UserSchoolAnchorCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    anchor = models.UserSchoolAnchor(
        user_id=current_user.id,
        institution_id=payload.institution_id,
        title=payload.title,
        description=payload.description,
        time_start_year=payload.time_start_year,
        time_end_year=payload.time_end_year,
        region_city=payload.region_city,
        region_district=payload.region_district,
    )
    db.add(anchor)
    db.commit()
    db.refresh(anchor)
    return anchor
