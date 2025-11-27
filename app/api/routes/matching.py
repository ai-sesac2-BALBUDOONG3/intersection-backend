# app/api/routes/matching.py
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.db import models  # User ORM은 여기서 사용
from app.schemas.matching import MatchRecommendation
from app.services import matching_service, matching_explanation

router = APIRouter(prefix="/match", tags=["matching"])


@router.get("/recommendations", response_model=List[MatchRecommendation])
def get_recommendations(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> List[MatchRecommendation]:
    """
    현재 로그인한 유저 기준 추천 친구 리스트 반환.
    - 점수 기반 필터링/정렬: DB 함수 match_recommendations
    - 추천 이유 한 줄: Azure OpenAI gpt-4o-mini
    """
    # 1) 점수 기반 후보 조회
    candidates = matching_service.get_match_recommendations(
        db=db,
        user_id=current_user.id,
        limit=limit,
    )

    # 2) GPT로 추천 이유 생성
    simple_user = matching_explanation.SimpleUserContext(
        id=current_user.id,
        nickname=current_user.nickname,
    )
    reasons = matching_explanation.generate_match_reasons(
        current_user=simple_user,
        candidates=candidates,
    )

    # 3) 각 후보에 reason 채워서 반환
    for c in candidates:
        c.reason = reasons.get(
            c.candidate_user_id,
            c.reason or "과거 같은 시기/지역에서 생활했던 인연일 가능성이 높아요.",
        )

    return candidates
