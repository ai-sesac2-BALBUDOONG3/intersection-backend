# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from dotenv import load_dotenv
import os

# 1) .env 로드
load_dotenv()

# 2) Azure Cosmos DB for PostgreSQL 연결 문자열
#    예) postgresql+psycopg2://user:password@host:port/dbname?sslmode=require
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "❌ DATABASE_URL 환경 변수가 설정되지 않았습니다. "
        ".env 파일에 DATABASE_URL을 추가해 주세요."
    )

# 3) SQLAlchemy 엔진 생성
#    - pool_pre_ping=True : 끊어진 커넥션 자동 감지
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

# 4) 세션 & Base
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
