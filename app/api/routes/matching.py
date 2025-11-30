# app/api/routes/matching.py

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.db import models
from app.db.session import get_db
from app.schemas.matching import (
    MatchRecommendation,
    OnboardingRequest,
    OnboardingResponse,
)
from app.services.embedding_service import refresh_anchor_embedding
from app.services.matching_service import get_match_recommendations
from app.services.matching_explanation import (
    SimpleUserContext,
    generate_match_reasons,
)

router = APIRouter(prefix="/match", tags=["matching"])


# ------------------------------------------------------
# 헬퍼: 추천 리스트에 GPT 추천이유 붙이기
# ------------------------------------------------------
def _attach_reasons_if_possible(
    current_user: models.User,
    recommendations: List[MatchRecommendation],
) -> List[MatchRecommendation]:
    """
    Azure OpenAI 설정이 되어 있으면 각 추천에 reason을 채워준다.
    설정이 없거나 에러가 나면 그냥 reason 없이 반환.
    """
    if not recommendations:
        return recommendations

    try:
        user_ctx = SimpleUserContext(
            id=current_user.id,
            nickname=current_user.nickname,
        )
        reasons = generate_match_reasons(user_ctx, recommendations)
    except Exception as e:
        # Azure OpenAI 설정이 없거나 에러가 나면 조용히 스킵
        print(f"[match] generate_match_reasons 실패: {e}")
        return recommendations

    for rec in recommendations:
        if rec.candidate_user_id in reasons:
            rec.reason = reasons[rec.candidate_user_id]

    return recommendations


# ------------------------------------------------------
# 1) 온보딩: 앵커 + 학교이력 + 키워드 저장 + 첫 추천
# ------------------------------------------------------
@router.post(
    "/onboarding",
    response_model=OnboardingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="온보딩: 대표 학교/이력/키워드 저장 후 추천친구 반환",
)
def create_onboarding_and_recommend(
    payload: OnboardingRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
    limit: int = Query(10, ge=1, le=50, description="추천 친구 최대 개수"),
) -> OnboardingResponse:
    """
    회원가입 직후 온보딩 화면에서 호출하는 API.

    1. user_school_histories 1건 생성
    2. user_school_anchors 1건 생성
    3. user_keywords 여러 건 생성
    4. 앵커 임베딩 생성 (Azure OpenAI)
    5. match_recommendations() 호출 → 추천 친구 추출
    6. gpt-4o-mini로 추천 이유 한 줄씩 생성 (가능한 경우)
    """

    # 1) 학교 이력 생성
    h = payload.history
    history = models.UserSchoolHistory(
        user_id=current_user.id,
        institution_id=h.institution_id,
        school_name_snapshot=h.school_name_snapshot,
        grade=h.grade,
        class_name=h.class_name,
        teacher_name=h.teacher_name,
        nickname_in_class=h.nickname_in_class,
        time_start_year=h.time_start_year,
        time_end_year=h.time_end_year,
        is_current=h.is_current,
        visibility=h.visibility,
    )
    db.add(history)
    db.flush()  # history.id 확보

    # 2) 대표 앵커 생성
    a = payload.anchor
    anchor = models.UserSchoolAnchor(
        user_id=current_user.id,
        institution_id=a.institution_id or h.institution_id,
        title=a.title,
        description=a.description,
        time_start_year=a.time_start_year or h.time_start_year,
        time_end_year=a.time_end_year or h.time_end_year,
        region_city=a.region_city,
        region_district=a.region_district,
    )
    db.add(anchor)
    db.flush()  # anchor.id 확보

    # 3) 키워드들 생성 (공백/중복 제거)
    created_keyword_ids: List[int] = []
    seen: set[str] = set()

    for raw_kw in payload.keywords:
        kw = (raw_kw or "").strip()
        if not kw:
            continue
        key = kw.lower()
        if key in seen:
            continue
        seen.add(key)

        keyword_row = models.UserKeyword(
            user_id=current_user.id,
            keyword=kw,
            # weight 기본값 1.0 그대로 사용
        )
        db.add(keyword_row)
        db.flush()
        created_keyword_ids.append(keyword_row.id)

    # 기본 데이터 저장 커밋
    db.commit()

    # 4) 앵커 임베딩 생성 (실패해도 전체 플로우는 진행)
    try:
        refresh_anchor_embedding(db, anchor_id=anchor.id)
    except Exception as e:
        print(f"[match] refresh_anchor_embedding 실패: {e}")

    # 5) 추천 친구 조회
    recommendations = get_match_recommendations(
        db=db,
        user_id=current_user.id,
        limit=limit,
    )

    # 6) 추천 이유 붙이기 (Azure OpenAI 설정 있는 경우만)
    recommendations = _attach_reasons_if_possible(
        current_user=current_user,
        recommendations=recommendations,
    )

    return OnboardingResponse(
        anchor_id=anchor.id,
        history_id=history.id,
        created_keyword_ids=created_keyword_ids,
        recommendations=recommendations,
    )


# ------------------------------------------------------
# 2) 일반 추천: 언제든 추천 친구 다시 보기
# ------------------------------------------------------
@router.get(
    "/recommendations",
    response_model=List[MatchRecommendation],
    summary="추천 친구 목록 조회",
)
def list_recommendations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_user),
    limit: int = Query(20, ge=1, le=50, description="추천 친구 최대 개수"),
    with_reasons: bool = Query(
        True,
        description="True면 Azure OpenAI로 추천 이유 한 줄 생성 (환경 설정 필요)",
    ),
) -> List[MatchRecommendation]:
    """
    - 이미 온보딩을 마친 유저가 '추천 친구 새로 고침' 할 때 사용하는 엔드포인트.
    - DB 함수 match_recommendations 를 호출해서 후보를 뽑는다.
    - with_reasons=True 이고 Azure OpenAI 설정이 되어 있으면, 각 후보에 추천 이유를 붙인다.
    """

    recommendations = get_match_recommendations(
        db=db,
        user_id=current_user.id,
        limit=limit,
    )

    if with_reasons:
        recommendations = _attach_reasons_if_possible(
            current_user=current_user,
            recommendations=recommendations,
        )

    return recommendations
