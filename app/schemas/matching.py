# app/schemas/matching.py
from typing import Optional
from pydantic import BaseModel, Field


class MatchScoreBreakdown(BaseModel):
    final_score: float = Field(..., description="최종 매칭 점수")
    school_score: float = Field(..., description="같은 학교 여부 점수")
    region_score: float = Field(..., description="지역(시/구) 기반 점수")
    year_score: float = Field(..., description="입학 연도 차이 기반 점수")
    keyword_score: float = Field(..., description="공통 키워드 기반 점수")
    embedding_score: float = Field(..., description="텍스트 임베딩 유사도 기반 점수")


class MatchRecommendation(BaseModel):
    candidate_user_id: int = Field(..., description="추천 대상 유저 ID")
    nickname: str = Field(..., description="추천 대상 유저 닉네임")
    # 필요 시 확장 가능 (예: 프로필 이미지, 소개 문구 등)
    # profile_image_url: Optional[str] = None

    scores: MatchScoreBreakdown
    reason: Optional[str] = Field(None, description="gpt-4o-mini가 생성한 추천 이유 한 줄")
