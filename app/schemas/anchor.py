# app/schemas/anchor.py

from typing import Optional
from pydantic import BaseModel, Field


class AnchorCreate(BaseModel):
    """
    클라이언트(Flutter)에서 대표 학교/기억 앵커를 생성할 때 보내는 요청 바디.
    """
    institution_id: Optional[int] = Field(
        None,
        description="학교/기관 ID (institutions.id). 선택한 학교가 없으면 null",
    )
    title: str = Field(
        ...,
        description="대표 앵커 제목 (예: '서울 강동초 6학년 3반 (2010~2012)')",
        min_length=1,
    )
    description: Optional[str] = Field(
        None,
        description="추가 설명 (담임 이름, 별명, 당시 동아리 등)",
    )
    time_start_year: Optional[int] = Field(
        None,
        description="기억 시작 연도 (예: 2010)",
        ge=1900,
        le=2100,
    )
    time_end_year: Optional[int] = Field(
        None,
        description="기억 종료 연도 (예: 2012)",
        ge=1900,
        le=2100,
    )
    region_city: Optional[str] = Field(
        None,
        description="도시/시 (예: '서울특별시')",
    )
    region_district: Optional[str] = Field(
        None,
        description="구/군 (예: '강동구')",
    )


class AnchorRead(BaseModel):
    """
    생성/조회 시 클라이언트로 내려가는 앵커 정보.
    """
    id: int = Field(..., description="앵커 ID (user_school_anchors.id)")
    institution_id: Optional[int] = Field(
        None,
        description="학교/기관 ID (institutions.id)",
    )
    title: str = Field(..., description="대표 앵커 제목")
    description: Optional[str] = Field(None, description="추가 설명")
    time_start_year: Optional[int] = Field(None, description="기억 시작 연도")
    time_end_year: Optional[int] = Field(None, description="기억 종료 연도")
    region_city: Optional[str] = Field(None, description="도시/시")
    region_district: Optional[str] = Field(None, description="구/군")
    has_embedding: bool = Field(
        ...,
        description="anchor_embedding 이 생성되었는지 여부",
    )

    class Config:
        from_attributes = True
