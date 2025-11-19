# path: database.py
import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, declarative_base

# 1) .env 로드
load_dotenv()

# 2) 환경변수에서 DB 연결 정보 읽기
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_SSLMODE = os.getenv("DB_SSLMODE", "require")  # Azure 기본값: require

if not DB_NAME or not DB_USER:
    raise RuntimeError(
        "❌ DB_NAME 또는 DB_USER 환경 변수가 설정되지 않았습니다. .env 파일을 확인해 주세요."
    )

# 3) SQLAlchemy용 URL 객체 생성
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",  # psycopg3
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
)

print(
    f"[DB] Using PostgreSQL at {DB_HOST}:{DB_PORT} / db={DB_NAME} / user={DB_USER}"
)

# 4) 엔진 / 세션 / Base 설정
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
    connect_args={"sslmode": DB_SSLMODE} if DB_SSLMODE else {},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


# 5) FastAPI 의존성 주입용
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 6) 헬스체크용 간단한 쿼리
def check_db_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:  # 실무에선 로깅
        print("[DB] Health check failed:", e)
        return False
