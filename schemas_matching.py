# path: schemas_matching.py
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class AnchorMatchCandidate(BaseModel):
    candidate_user_id: int
    candidate_nickname: str
    similarity_score: float

    school_name: Optional[str] = None
    school_level: Optional[str] = None
    entry_year: Optional[int] = None
    graduation_year: Optional[int] = None
    region_city: Optional[str] = None
    region_district: Optional[str] = None

    overlap_fragments: List[str] = []
    extra_hint: Optional[str] = None
    explanation: Optional[str] = None


class AnchorMatchResponse(BaseModel):
    total: int
    top_k: int
    min_similarity: float
    candidates: List[AnchorMatchCandidate]
