# app/api/routes/school_histories.py

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.user_school_history import UserSchoolHistory
from app.schemas.school_history import (
    UserSchoolHistoryCreate,
    UserSchoolHistoryRead,
)

router = APIRouter(
    prefix="/school-histories",
    tags=["school_histories"],
)


@router.post(
    "",
    response_model=UserSchoolHistoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="나의 학교 기억 조각 추가",
)
def create_school_history(
    payload: UserSchoolHistoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    history = UserSchoolHistory(
        user_id=current_user.id,
        institution_id=payload.institution_id,
        school_name=payload.school_name,
        region_city=payload.region_city,
        region_district=payload.region_district,
        time_start_year=payload.time_start_year,
        time_end_year=payload.time_end_year,
        grade=payload.grade,
        class_name=payload.class_name,
        homeroom_teacher_name=payload.homeroom_teacher_name,
        memo=payload.memo,
    )

    db.add(history)
    db.commit()
    db.refresh(history)

    return UserSchoolHistoryRead.model_validate(history)


@router.get(
    "/me",
    response_model=List[UserSchoolHistoryRead],
    summary="내 학교 기억 조각 목록 조회",
)
def list_my_school_histories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    histories = (
        db.query(UserSchoolHistory)
        .filter(
            UserSchoolHistory.user_id == current_user.id,
            UserSchoolHistory.is_deleted == False,  # noqa: E712
        )
        .order_by(
            UserSchoolHistory.time_start_year.asc().nulls_last(),  # type: ignore[attr-defined]
            UserSchoolHistory.created_at.asc(),
        )
        .all()
    )

    return [
        UserSchoolHistoryRead.model_validate(h) for h in histories
    ]
