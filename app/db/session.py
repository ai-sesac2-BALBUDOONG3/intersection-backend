from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.settings import get_settings

settings = get_settings()

# ===== SQLAlchemy Base =====
Base = declarative_base()

# ===== Engine / Session =====
# Azure PostgreSQL 접속 (sslmode=require 는 settings.database_url 에 이미 포함)
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)


def get_db() -> Generator:
    """
    FastAPI 의존성으로 사용하는 DB 세션 생성기.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
