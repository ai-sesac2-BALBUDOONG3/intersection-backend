# path: database.py
"""
로컬 PostgreSQL(inter_section) 전용 DB 설정

- .env 의 DATABASE_URL 값을 그대로 사용
- SQLAlchemy SessionLocal / Base / 헬스체크 유틸 제공
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

# .env 로드
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL 환경변수가 설정되어 있지 않습니다. "
        "예: postgresql://postgres:password@localhost:5432/inter_section"
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    future=True,
)

Base = declarative_base()


def get_db():
    """FastAPI Depends 에서 사용하는 DB 세션."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_health() -> dict:
    """DB 헬스체크 유틸."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"ok": True, "url": DATABASE_URL}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


if __name__ == "__main__":
    """
    로컬 개발용 스키마 생성 헬퍼.
    최초 한 번 DB에 테이블을 생성할 때만 실행하는 것을 권장.
    """
    import models  # noqa: F401  # 모델 로딩용

    print("[database] Creating all tables on local PostgreSQL...")
    Base.metadata.create_all(bind=engine)
    print("[database] Done.")
