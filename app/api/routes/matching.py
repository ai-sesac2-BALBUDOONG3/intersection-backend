# app/api/routes/matching.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.user_school_history import UserSchoolHistory
from app.schemas.matching import MatchCandidateRead

router = APIRouter(
    prefix="/match",
    tags=["match"],
)


@router.get(
    "/candidates",
    response_model=List[MatchCandidateRead],
    summary="학교/시기 기반 매칭 후보 조회",
)
def get_match_candidates(
    base_school_history_id: int = Query(..., description="내 기준이 되는 school_history id"),
    limit: int = Query(20, ge=1, le=100, description="최대 후보 수"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    1. base_school_history_id가 **현재 로그인 유저의 기록인지** 검증
    2. 같은 학교(institution_id 또는 school_name 기준) + 시기 겹치는 사람들 중
       현재 유저가 아닌 다른 유저들을 후보로 반환
    """

    base: UserSchoolHistory | None = (
        db.query(UserSchoolHistory)
        .filter(
            UserSchoolHistory.id == base_school_history_id,
            UserSchoolHistory.user_id == current_user.id,
            UserSchoolHistory.is_deleted == False,  # noqa: E712
        )
        .first()
    )

    if base is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 school_history가 존재하지 않거나 현재 유저의 기록이 아닙니다.",
        )

    # 필터용 파라미터 준비
    institution_id = base.institution_id
    school_name = base.school_name
    region_city = base.region_city
    region_district = base.region_district
    time_start_year = base.time_start_year
    time_end_year = base.time_end_year

    sql = text(
        """
        SELECT
            u.id AS user_id,
            u.nickname,
            u.real_name,
            u.email,
            h.id AS school_history_id,
            h.school_name,
            h.region_city,
            h.region_district,
            h.time_start_year,
            h.time_end_year,
            h.grade,
            h.class_name,
            h.homeroom_teacher_name
        FROM user_school_histories h
        JOIN users u ON u.id = h.user_id
        WHERE h.is_deleted = false
          AND h.user_id <> :current_user_id
          -- 같은 학교 (institution_id 우선, 없으면 school_name)
          AND (
                (:institution_id IS NOT NULL AND h.institution_id = :institution_id)
             OR (
                    :institution_id IS NULL
                AND h.institution_id IS NULL
                AND h.school_name = :school_name
             )
          )
          -- 같은/비슷한 지역이면 가중
          AND (
                :region_city IS NULL
             OR h.region_city IS NULL
             OR h.region_city = :region_city
          )
          AND (
                :region_district IS NULL
             OR h.region_district IS NULL
             OR h.region_district = :region_district
          )
          -- 시기 겹침 체크 (둘 다 연도가 있을 때만)
          AND (
                :time_start_year IS NULL
             OR :time_end_year IS NULL
             OR h.time_start_year IS NULL
             OR h.time_end_year IS NULL
             OR (h.time_start_year <= :time_end_year AND h.time_end_year >= :time_start_year)
          )
        ORDER BY
            h.time_start_year NULLS LAST,
            h.created_at
        LIMIT :limit
        """
    )

    rows = db.execute(
        sql,
        {
            "current_user_id": current_user.id,
            "institution_id": institution_id,
            "school_name": school_name,
            "region_city": region_city,
            "region_district": region_district,
            "time_start_year": time_start_year,
            "time_end_year": time_end_year,
            "limit": limit,
        },
    ).mappings().all()

    return [MatchCandidateRead(**row) for row in rows]
