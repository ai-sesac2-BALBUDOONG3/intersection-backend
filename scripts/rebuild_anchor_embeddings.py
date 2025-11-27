# scripts/rebuild_anchor_embeddings.py

"""
Intersection - user_school_anchors 임베딩 일괄 생성 스크립트.

사용 예시 (프로젝트 루트에서):

    # 가상환경 활성화 후
    # python -m scripts.rebuild_anchor_embeddings

전제:
    - app.db.session.SessionLocal 이 정의되어 있고,
    - DB / Azure OpenAI 관련 환경변수가 설정되어 있어야 한다.
"""

from app.db.session import SessionLocal
from app.services.embedding_service import rebuild_missing_anchor_embeddings


def main() -> None:
    db = SessionLocal()
    try:
        stats = rebuild_missing_anchor_embeddings(db=db, batch_size=100)
        print(
            f"[anchor embeddings rebuild] "
            f"processed={stats['processed']}, "
            f"succeeded={stats['succeeded']}, "
            f"failed={stats['failed']}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
