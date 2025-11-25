# app/services/matching_service.py
from __future__ import annotations

from typing import List, Tuple, Optional

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.db import models
from app.schemas.matching import AnchorMatchCandidate


def _cosine_similarity(a: Optional[list[float]], b: Optional[list[float]]) -> float:
    if not a or not b or len(a) == 0 or len(b) == 0 or len(a) != len(b):
        return 0.0
    import math

    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def find_anchor_matches(
    db: Session,
    base_user: models.User,
    limit: int = 20,
) -> List[AnchorMatchCandidate]:
    """
    1) base_user의 앵커들을 가져오고
    2) institution/기간/지역 기준으로 후보 앵커 필터
    3) 임베딩 있으면 코사인 유사도, 없으면 0
    4) 상위 N명 반환
    """
    # 자기 앵커
    base_anchors = (
        db.execute(
            select(models.UserSchoolAnchor)
            .where(
                models.UserSchoolAnchor.user_id == base_user.id,
                models.UserSchoolAnchor.is_deleted == False,
            )
        )
        .scalars()
        .all()
    )

    if not base_anchors:
        return []

    # 후보 앵커: 자기 제외, 삭제 제외, 상태 active인 user만
    # (필터는 SQL + 파이썬 혼합)
    candidates: List[AnchorMatchCandidate] = []

    for base_anchor in base_anchors:
        # coarse filter
        filters = [
            models.UserSchoolAnchor.user_id != base_user.id,
            models.UserSchoolAnchor.is_deleted == False,
        ]

        if base_anchor.institution_id:
            filters.append(models.UserSchoolAnchor.institution_id == base_anchor.institution_id)
        if base_anchor.time_start_year and base_anchor.time_end_year:
            filters.append(
                and_(
                    models.UserSchoolAnchor.time_start_year <= base_anchor.time_end_year,
                    models.UserSchoolAnchor.time_end_year >= base_anchor.time_start_year,
                )
            )
        if base_anchor.region_city:
            filters.append(models.UserSchoolAnchor.region_city == base_anchor.region_city)
        if base_anchor.region_district:
            filters.append(models.UserSchoolAnchor.region_district == base_anchor.region_district)

        q = (
            select(models.UserSchoolAnchor, models.User, models.Institution)
            .join(models.User, models.UserSchoolAnchor.user_id == models.User.id)
            .join(models.Institution, models.UserSchoolAnchor.institution_id == models.Institution.id, isouter=True)
            .where(
                *filters,
                models.User.status == "active",
                models.User.is_deleted == False,
            )
        )

        for anchor, user, inst in db.execute(q).all():
            score = _cosine_similarity(base_anchor.anchor_embedding, anchor.anchor_embedding)
            institution_name = inst.name if inst else None

            overlap_start = None
            overlap_end = None
            if (
                base_anchor.time_start_year
                and base_anchor.time_end_year
                and anchor.time_start_year
                and anchor.time_end_year
            ):
                overlap_start = max(base_anchor.time_start_year, anchor.time_start_year)
                overlap_end = min(base_anchor.time_end_year, anchor.time_end_year)

            candidate = AnchorMatchCandidate(
                target_user_id=user.id,
                target_user_nickname=user.nickname,
                target_anchor_id=anchor.id,
                target_anchor_title=anchor.title,
                institution_name=institution_name,
                overlap_start_year=overlap_start,
                overlap_end_year=overlap_end,
                region_city=anchor.region_city,
                region_district=anchor.region_district,
                score=score,
            )
            candidates.append(candidate)

    # 동일 유저/앵커 중복 제거 + 점수 정렬
    # (간단하게 score 기준으로 정렬)
    unique: dict[Tuple[int, int], AnchorMatchCandidate] = {}
    for c in candidates:
        key = (c.target_user_id, c.target_anchor_id)
        if key not in unique or c.score > unique[key].score:
            unique[key] = c

    ranked = sorted(unique.values(), key=lambda x: x.score, reverse=True)
    return ranked[:limit]
