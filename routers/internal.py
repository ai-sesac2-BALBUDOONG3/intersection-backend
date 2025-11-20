# path: routers/internal.py
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

import ai_service
from deps import get_db_session
from embedding_jobs import reindex_school_anchors

router = APIRouter(tags=["internal"])


class TextIn(BaseModel):
    text: str


@router.post("/internal/test-embedding")
def internal_test_embedding(payload: TextIn):
    """
    Azure OpenAI 임베딩 동작 확인용 내부 API.
    - 입력 텍스트에 대해 벡터 차원 수와 앞 일부만 리턴.
    """
    embedding = ai_service.get_text_embedding(payload.text)
    return {
        "dim": len(embedding),
        "preview": embedding[:8],
    }


class MatchExplainIn(BaseModel):
    me_nickname: str
    candidate_nickname: str
    overlaps: List[str]
    extra_hint: Optional[str] = None


@router.post("/internal/test-match-explanation")
def internal_test_match_explanation(payload: MatchExplainIn):
    """
    기억 교집합 설명 생성용 내부 API.
    - overlaps: 교집합 설명 리스트
    """
    explanation = ai_service.build_match_explanation(
        me_nickname=payload.me_nickname,
        candidate_nickname=payload.candidate_nickname,
        overlap_fragments=payload.overlaps,
        extra_hint=payload.extra_hint,
    )
    return {"explanation": explanation}


class ReindexAnchorsIn(BaseModel):
    user_id: Optional[int] = None  # 특정 유저만 재색인하고 싶을 때 사용


@router.post("/internal/reindex/school-anchors")
def internal_reindex_school_anchors(
    payload: ReindexAnchorsIn,
    db: Session = Depends(get_db_session),
):
    """
    user_school_anchors.anchor_embedding 재생성용 내부 API.

    - payload.user_id 가 있으면 해당 유저의 앵커만
    - 없으면 전체 앵커 재색인
    """
    updated = reindex_school_anchors(db, user_id=payload.user_id)
    return {"updated": updated}
