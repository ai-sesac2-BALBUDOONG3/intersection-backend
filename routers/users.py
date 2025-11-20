# path: routers/users.py
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import crud
import models
import schemas
from deps import get_db_session, get_current_user

router = APIRouter()


# ---------------------------------------------------------------------------
# Profile / School Anchors / Keywords
# ---------------------------------------------------------------------------


@router.put(
    "/users/me/profile",
    response_model=schemas.UserProfile,
    tags=["profile"],
)
def update_profile(
    body: schemas.UserProfileUpdate,
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user),
):
    """사용자 프로필(거주지 등) 업서트."""
    profile = crud.upsert_user_profile(db, user_id=current_user.id, profile_in=body)
    return profile


@router.post(
    "/users/me/school-anchors",
    response_model=schemas.UserSchoolAnchor,
    tags=["school"],
)
def add_school_anchor(
    body: schemas.UserSchoolAnchorCreate,
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user),
):
    """
    대표 학교 앵커 추가.
    (임베딩은 별도 reindex 엔드포인트에서 생성)
    """
    anchor = crud.create_user_school_anchor(
        db, user_id=current_user.id, anchor_in=body
    )
    return anchor


@router.get(
    "/users/me/school-anchors",
    response_model=List[schemas.UserSchoolAnchor],
    tags=["school"],
)
def list_my_school_anchors(
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user),
):
    """내 대표 학교 앵커 리스트."""
    anchors = crud.list_user_school_anchors(db, user_id=current_user.id)
    return anchors


@router.post(
    "/users/me/keywords",
    response_model=schemas.UserKeyword,
    tags=["keywords"],
)
def add_keyword(
    body: schemas.UserKeywordCreate,
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user),
):
    """나를 설명하는 키워드 추가."""
    kw = crud.add_user_keyword(db, user_id=current_user.id, keyword_in=body)
    return kw


@router.get(
    "/users/me/keywords",
    response_model=List[schemas.UserKeyword],
    tags=["keywords"],
)
def list_keywords(
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user),
):
    """내 키워드 리스트."""
    kws = crud.list_user_keywords(db, user_id=current_user.id)
    return kws
