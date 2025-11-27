# app/services/matching_service.py
from typing import List
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.matching import MatchRecommendation, MatchScoreBreakdown


def get_match_recommendations(
    db: Session,
    user_id: int,
    limit: int = 20,
) -> List[MatchRecommendation]:
    """
    DB 함수 match_recommendations(p_user_id, p_limit)를 호출하여
    후보 유저 + 점수 정보를 가져온 뒤, Pydantic 모델 리스트로 변환.
    """
    sql = text(
        """
        SELECT
            m.candidate_user_id,
            m.final_score,
            m.school_score,
            m.region_score,
            m.year_score,
            m.keyword_score,
            m.embedding_score,
            u.nickname
        FROM match_recommendations(:user_id, :limit) AS m
        JOIN users u ON u.id = m.candidate_user_id
        ORDER BY m.final_score DESC
        """
    )

    rows = db.execute(sql, {"user_id": user_id, "limit": limit}).mappings().all()

    recommendations: List[MatchRecommendation] = []

    for row in rows:
        scores = MatchScoreBreakdown(
            final_score=float(row["final_score"]),
            school_score=float(row["school_score"]),
            region_score=float(row["region_score"]),
            year_score=float(row["year_score"]),
            keyword_score=float(row["keyword_score"]),
            embedding_score=float(row["embedding_score"]),
        )

        rec = MatchRecommendation(
            candidate_user_id=row["candidate_user_id"],
            nickname=row["nickname"],
            scores=scores,
            reason=None,  # 이후 gpt-4o-mini로 채움
        )
        recommendations.append(rec)

    return recommendations
