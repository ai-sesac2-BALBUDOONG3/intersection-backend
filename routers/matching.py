# path: routers/matching.py
from __future__ import annotations

from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import models
from deps import get_db_session, get_current_user
from matching_service import (
    AnchorMatchResult,
    find_anchor_matches_for_user,
    enrich_matches_with_explanations,
)
from schemas_matching import AnchorMatchResponse, AnchorMatchCandidate

router = APIRouter(prefix="/matching", tags=["matching"])


@router.get("/anchors", response_model=AnchorMatchResponse)
def get_anchor_matches(
    top_k: int = Query(20, ge=1, le=50, description="최대 후보 수 (기본 20, 최대 50)"),
    min_similarity: float = Query(
        0.3,
        ge=0.0,
        le=1.0,
        description="최소 유사도(0~1). 기본 0.3 이상만 노출",
    ),
    school_level: Optional[str] = Query(
        None, description="필터용 학제(ex: 'elementary', 'middle', 'high' 등)"
    ),
    entry_year_from: Optional[int] = Query(
        None, ge=1900, le=2100, description="입학년도 최소값"
    ),
    entry_year_to: Optional[int] = Query(
        None, ge=1900, le=2100, description="입학년도 최대값"
    ),
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user),
):
    """
    학교 앵커 기반 매칭(코사인 유사도) – LLM 설명 없이 순수 매칭 결과만 반환.
    """
    if (
        entry_year_from is not None
        and entry_year_to is not None
        and entry_year_from > entry_year_to
    ):
        raise HTTPException(
            status_code=400,
            detail="entry_year_from은 entry_year_to보다 클 수 없습니다.",
        )

    matches: List[AnchorMatchResult] = find_anchor_matches_for_user(
        db=db,
        current_user_id=current_user.id,
        top_k=top_k,
        min_similarity=min_similarity,
        school_level=school_level,
        entry_year_from=entry_year_from,
        entry_year_to=entry_year_to,
    )

    candidates = [
        AnchorMatchCandidate(
            candidate_user_id=m.candidate_user_id,
            candidate_nickname=m.candidate_nickname,
            similarity_score=round(float(m.similarity_score), 4),
            school_name=m.school_name,
            school_level=m.school_level,
            entry_year=m.entry_year,
            graduation_year=m.graduation_year,
            region_city=m.region_city,
            region_district=m.region_district,
            overlap_fragments=m.overlap_fragments,
            extra_hint=m.extra_hint,
            explanation=None,  # 이 엔드포인트에서는 설명 미포함
        )
        for m in matches
    ]

    return AnchorMatchResponse(
        total=len(candidates),
        top_k=top_k,
        min_similarity=min_similarity,
        candidates=candidates,
    )


@router.get("/anchors-with-explanation", response_model=AnchorMatchResponse)
def get_anchor_matches_with_explanation(
    top_k: int = Query(10, ge=1, le=20, description="LLM 설명을 붙일 후보 수 (기본 10, 최대 20)"),
    min_similarity: float = Query(
        0.3, ge=0.0, le=1.0, description="최소 유사도(0~1). 기본 0.3 이상만 노출"
    ),
    school_level: Optional[str] = Query(
        None, description="필터용 학제(ex: 'elementary', 'middle', 'high' 등)"
    ),
    entry_year_from: Optional[int] = Query(
        None, ge=1900, le=2100, description="입학년도 최소값"
    ),
    entry_year_to: Optional[int] = Query(
        None, ge=1900, le=2100, description="입학년도 최대값"
    ),
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user),
):
    """
    학교 앵커 기반 매칭 + Azure OpenAI로 자연어 설명까지 포함.
    """
    if (
        entry_year_from is not None
        and entry_year_to is not None
        and entry_year_from > entry_year_to
    ):
        raise HTTPException(
            status_code=400,
            detail="entry_year_from은 entry_year_to보다 클 수 없습니다.",
        )

    matches: List[AnchorMatchResult] = find_anchor_matches_for_user(
        db=db,
        current_user_id=current_user.id,
        top_k=top_k,
        min_similarity=min_similarity,
        school_level=school_level,
        entry_year_from=entry_year_from,
        entry_year_to=entry_year_to,
    )

    # LLM 설명 붙이기 (top_k 개수까지만)
    matches = enrich_matches_with_explanations(
        db=db,
        current_user_id=current_user.id,
        matches=matches,
        max_candidates=top_k,
    )

    candidates = [
        AnchorMatchCandidate(
            candidate_user_id=m.candidate_user_id,
            candidate_nickname=m.candidate_nickname,
            similarity_score=round(float(m.similarity_score), 4),
            school_name=m.school_name,
            school_level=m.school_level,
            entry_year=m.entry_year,
            graduation_year=m.graduation_year,
            region_city=m.region_city,
            region_district=m.region_district,
            overlap_fragments=m.overlap_fragments,
            extra_hint=m.extra_hint,
            explanation=m.explanation,
        )
        for m in matches
    ]

    return AnchorMatchResponse(
        total=len(candidates),
        top_k=top_k,
        min_similarity=min_similarity,
        candidates=candidates,
    )
