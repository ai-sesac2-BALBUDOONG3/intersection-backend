# path: reset_schema.py
from sqlalchemy import text

from database import engine
import models  # noqa: F401  (Base 에 테이블 등록용)


def main():
    print("[reset] 기존 테이블을 드롭하고 새 스키마로 재생성합니다.")

    drop_sql = """
    DROP TABLE IF EXISTS
        community_comments,
        community_posts,
        community_members,
        communities,
        reports,
        user_keywords,
        user_school_histories,
        user_school_anchors,
        user_profiles,
        user_blocks,
        user_friendships,
        institution_raw,
        sync_jobs,
        institutions,
        users
    CASCADE;
    """

    with engine.begin() as conn:
        conn.execute(text(drop_sql))
        print("[reset] 기존 테이블 DROP 완료.")
        models.Base.metadata.create_all(bind=conn)
        print("[reset] 새 스키마 CREATE_ALL 완료.")

    print("[reset] 완료!")


if __name__ == "__main__":
    main()
