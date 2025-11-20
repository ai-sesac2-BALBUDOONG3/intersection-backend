# path: matching_service.py
from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

import models  # 기존 models.py 사용
import ai_service  # 기존 ai_service.py 사용

logger = logging.getLogger(__name__)


@dataclass
class AnchorMatchResult:
    """DB에서 나온 매칭 결과(후보 1명당 1개)"""

    candidate_user_id: int
    candidate_nickname: str
    similarity_score: float

    school_name: Optional[str] = None
    school_level: Optional[str] = None
    entry_year: Optional[int] = None
    graduation_year: Optional[int] = None
    region_city: Optional[str] = None
    region_district: Optional[str] = None

    overlap_fragments: List[str] = field(default_factory=list)
    extra_hint: Optional[str] = None
    explanation: Optional[str] = None

    def build_overlap_fragments(self) -> List[str]:
        """LLM 설명에 넣을 '겹치는 학교/시기' 한 줄 설명들을 만든다."""
        fragments: List[str] = []

        if self.school_name:
            loc_parts: List[str] = []
            if self.region_city:
                loc_parts.append(self.region_city)
            if self.region_district:
                loc_parts.append(self.region_district)

            loc_str = " ".join(loc_parts)
            school_part = f"{loc_str} {self.school_name}" if loc_str else self.school_name

            if self.entry_year and self.graduation_year:
                fragments.append(f"{school_part}, {self.entry_year}~{self.graduation_year}년 재학")
            elif self.entry_year:
                fragments.append(f"{school_part}, {self.entry_year}년 입학")
            else:
                fragments.append(school_part)

        return fragments


def _user_has_anchor_embeddings(db: Session, user_id: int) -> bool:
    """현재 유저가 임베딩이 채워진 앵커를 1개라도 갖고 있는지 검사."""
    row = db.execute(
        text(
            """
            SELECT 1
            FROM user_school_anchors
            WHERE user_id = :uid
              AND anchor_embedding IS NOT NULL
            LIMIT 1;
            """
        ),
        {"uid": user_id},
    ).first()
    return row is not None


def find_anchor_matches_for_user(
    db: Session,
    current_user_id: int,
    top_k: int = 20,
    min_similarity: float = 0.3,
    school_level: Optional[str] = None,
    entry_year_from: Optional[int] = None,
    entry_year_to: Optional[int] = None,
) -> List[AnchorMatchResult]:
    """
    현재 로그인 유저 기준으로 학교 앵커 기반 코사인 유사도 매칭.

    - pgvector의 코사인 distance 연산자 `<=>`를 사용한다고 가정 (vector_cosine_ops 인덱스 권장)
    - 유사도 = 1 - cosine_distance
    - 유저 단위로 그룹핑, MAX similarity 기준으로 대표 앵커 선택
    """

    if top_k <= 0:
        return []

    if not _user_has_anchor_embeddings(db, current_user_id):
        logger.info("User %s has no anchor embeddings; skip matching.", current_user_id)
        return []

    # 동적 필터 문자열(바인딩은 모두 파라미터로 처리)
    school_level_filter = "AND c.school_level = :school_level" if school_level else ""
    entry_year_from_filter = (
        "AND c.entry_year >= :entry_year_from" if entry_year_from is not None else ""
    )
    entry_year_to_filter = (
        "AND c.entry_year <= :entry_year_to" if entry_year_to is not None else ""
    )

    # Cosmos DB for PostgreSQL + pgvector 기준 쿼리
    # - self_anchors: 현재 유저의 앵커
    # - candidate_anchors: 다른 유저들의 앵커 (차단/비활성/삭제 제외)
    # - 코사인 distance 연산자 `<=>`를 사용하고, similarity = 1 - distance
    base_sql = f"""
        WITH self_anchors AS (
            SELECT
                anchor_embedding,
                school_level,
                entry_year,
                graduation_year,
                institution_id
            FROM user_school_anchors
            WHERE user_id = :current_user_id
              AND anchor_embedding IS NOT NULL
        ),
        candidate_anchors AS (
            SELECT
                a.id,
                a.user_id,
                a.school_level,
                a.entry_year,
                a.graduation_year,
                a.institution_id,
                a.anchor_embedding,
                u.nickname,
                i.name          AS school_name,
                i.region_city   AS region_city,
                i.region_district AS region_district
            FROM user_school_anchors a
            JOIN users u
              ON u.id = a.user_id
            LEFT JOIN institutions i
              ON i.id = a.institution_id
            LEFT JOIN user_blocks b1
              ON b1.blocker_id = :current_user_id
             AND b1.blocked_id = a.user_id
            LEFT JOIN user_blocks b2
              ON b2.blocker_id = a.user_id
             AND b2.blocked_id = :current_user_id
            WHERE a.user_id != :current_user_id
              AND a.anchor_embedding IS NOT NULL
              AND u.status = 'active'
              AND COALESCE(u.is_deleted, FALSE) = FALSE
              AND b1.id IS NULL
              AND b2.id IS NULL
        )
        SELECT
            c.user_id AS candidate_user_id,
            -- 후보 유저 전체 앵커 중, 내 앵커들과의 최대 코사인 유사도
            MAX(1 - (s.anchor_embedding <=> c.anchor_embedding)) AS similarity_score,
            -- 최대 유사도를 주는 앵커를 대표로 사용
            (ARRAY_AGG(c.nickname ORDER BY (1 - (s.anchor_embedding <=> c.anchor_embedding)) DESC))[1]
                AS candidate_nickname,
            (ARRAY_AGG(c.school_name ORDER BY (1 - (s.anchor_embedding <=> c.anchor_embedding)) DESC))[1]
                AS school_name,
            (ARRAY_AGG(c.school_level ORDER BY (1 - (s.anchor_embedding <=> c.anchor_embedding)) DESC))[1]
                AS school_level,
            (ARRAY_AGG(c.entry_year ORDER BY (1 - (s.anchor_embedding <=> c.anchor_embedding)) DESC))[1]
                AS entry_year,
            (ARRAY_AGG(c.graduation_year ORDER BY (1 - (s.anchor_embedding <=> c.anchor_embedding)) DESC))[1]
                AS graduation_year,
            (ARRAY_AGG(c.region_city ORDER BY (1 - (s.anchor_embedding <=> c.anchor_embedding)) DESC))[1]
                AS region_city,
            (ARRAY_AGG(c.region_district ORDER BY (1 - (s.anchor_embedding <=> c.anchor_embedding)) DESC))[1]
                AS region_district
        FROM self_anchors s
        JOIN candidate_anchors c ON TRUE
        WHERE 1 = 1
          {school_level_filter}
          {entry_year_from_filter}
          {entry_year_to_filter}
        GROUP BY c.user_id
        HAVING MAX(1 - (s.anchor_embedding <=> c.anchor_embedding)) >= :min_similarity
        ORDER BY similarity_score DESC
        LIMIT :top_k;
    """

    params = {
        "current_user_id": current_user_id,
        "top_k": top_k,
        "min_similarity": min_similarity,
    }
    if school_level:
        params["school_level"] = school_level
    if entry_year_from is not None:
        params["entry_year_from"] = entry_year_from
    if entry_year_to is not None:
        params["entry_year_to"] = entry_year_to

    rows = db.execute(text(base_sql), params).fetchall()

    results: List[AnchorMatchResult] = []
    for row in rows:
        # row는 KeyedTuple이므로 dict(row)로 변환 가능
        data = dict(row._mapping) if hasattr(row, "_mapping") else dict(row)
        result = AnchorMatchResult(
            candidate_user_id=data["candidate_user_id"],
            candidate_nickname=data["candidate_nickname"],
            similarity_score=float(data["similarity_score"]),
            school_name=data.get("school_name"),
            school_level=data.get("school_level"),
            entry_year=data.get("entry_year"),
            graduation_year=data.get("graduation_year"),
            region_city=data.get("region_city"),
            region_district=data.get("region_district"),
        )
        # 학교/시기 정보를 기반으로 overlap_fragments 초기 세팅
        result.overlap_fragments = result.build_overlap_fragments()
        results.append(result)

    logger.info(
        "Anchor matching for user %s -> %s candidates (top_k=%s, min_similarity=%.3f)",
        current_user_id,
        len(results),
        top_k,
        min_similarity,
    )
    return results


def enrich_matches_with_explanations(
    db: Session,
    current_user_id: int,
    matches: List[AnchorMatchResult],
    max_candidates: int = 20,
) -> List[AnchorMatchResult]:
    """
    LLM을 이용해 각 매칭 후보에 자연어 설명을 붙인다.

    - top_k(또는 max_candidates)까지만 설명 생성 (과도한 비용 방지)
    - Azure OpenAI 에러 발생 시 fallback 메시지로 대체
    """

    if not matches:
        return matches

    # 내 닉네임 가져오기 (없으면 '나' 사용)
    me: Optional[models.User] = (
        db.query(models.User).filter(models.User.id == current_user_id).first()
    )
    me_nickname = (me.nickname or "나") if me else "나"

    # LLM 호출 수를 제한
    limited_matches = matches[:max_candidates]

    for m in limited_matches:
        # 이미 build_overlap_fragments로 기본 overlap_fragments는 세팅됨.
        if not m.overlap_fragments:
            m.overlap_fragments = m.build_overlap_fragments()

        # 추가 힌트: 상대방 UserKeyword 상위 3개 정도를 간단히 모아준다.
        try:
            keywords = (
                db.query(models.UserKeyword)
                .filter(models.UserKeyword.user_id == m.candidate_user_id)
                .order_by(models.UserKeyword.weight.desc())
                .limit(3)
                .all()
            )
        except Exception:  # 안전하게 방어
            logger.exception(
                "Failed to load UserKeyword for candidate %s", m.candidate_user_id
            )
            keywords = []

        if keywords:
            kw_text = ", ".join(
                k.keyword for k in keywords if getattr(k, "keyword", None)
            )
            if kw_text:
                m.extra_hint = f"상대방 대표 키워드: {kw_text}"
        else:
            m.extra_hint = None

        try:
            # ai_service.build_match_explanation 함수 시그니처에 맞춰 호출
            m.explanation = ai_service.build_match_explanation(
                me_nickname=me_nickname,
                candidate_nickname=m.candidate_nickname,
                overlap_fragments=m.overlap_fragments,
                extra_hint=m.extra_hint,
            )
        except Exception:
            logger.exception(
                "Failed to build match explanation for candidate %s",
                m.candidate_user_id,
            )
            m.explanation = "설명 생성에 실패했습니다. 잠시 후 다시 시도해주세요."

    return matches
