# path: embedding_jobs.py
"""
user_school_anchors 임베딩 생성/갱신 배치 유틸.

- reindex_school_anchors(db, user_id=None)
"""

from typing import Optional

from sqlalchemy.orm import Session, joinedload

import models
from ai_service import get_text_embedding


def build_anchor_text(anchor: models.UserSchoolAnchor) -> str:
    """
    한 앵커를 설명하는 텍스트를 만들어서 임베딩 입력으로 사용.
    (필요하면 나중에 더 풍부하게 조합 가능)
    """
    inst: models.Institution | None = anchor.institution  # relationship 가정
    user: models.User | None = anchor.user

    parts: list[str] = []

    if inst:
        parts.append(f"{inst.name}")
        if inst.region_city:
            parts.append(inst.region_city)
        if inst.region_district:
            parts.append(inst.region_district)

    # 학제 + 재학 연도
    parts.append(f"{anchor.school_level} 재학")
    parts.append(f"{anchor.entry_year}년 입학 ~ {anchor.graduation_year}년 졸업 예정/졸업")

    if user:
        parts.append(f"사용자 닉네임: {user.nickname}")

    text = " / ".join(parts)
    return text


def reindex_school_anchors(
    db: Session,
    user_id: Optional[int] = None,
    batch_size: int = 100,
) -> int:
    """
    user_school_anchors의 anchor_embedding을 재생성.

    - user_id가 주어지면 해당 유저 anchers만
    - 아니면 전체
    반환값: 처리한 앵커 수
    """
    query = (
        db.query(models.UserSchoolAnchor)
        .options(
            joinedload(models.UserSchoolAnchor.institution),
            joinedload(models.UserSchoolAnchor.user),
        )
        .order_by(models.UserSchoolAnchor.id)
    )

    if user_id is not None:
        query = query.filter(models.UserSchoolAnchor.user_id == user_id)

    total_updated = 0

    offset = 0
    while True:
        batch = query.offset(offset).limit(batch_size).all()
        if not batch:
            break

        for anchor in batch:
            text = build_anchor_text(anchor)
            embedding = get_text_embedding(text)
            anchor.anchor_embedding = embedding

        db.commit()
        total_updated += len(batch)
        offset += batch_size

    return total_updated
