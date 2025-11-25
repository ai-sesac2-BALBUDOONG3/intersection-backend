# app/db/session.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

# Azure PostgreSQL Flexible Server용 엔진
engine = create_engine(
    settings.sqlalchemy_database_uri,
    pool_pre_ping=True,   # 죽은 커넥션 자동 감지
    pool_size=5,
    max_overflow=10,
    future=True,
)

# 세션 팩토리
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)

# Base: 모델들이 여기서 상속받는다고 가정 (기존 모델에서 import해서 사용)
Base = declarative_base()


def get_db():
    """
    FastAPI 의 Depends 에서 사용할 DB 세션 의존성.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
