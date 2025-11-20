# path: main.py
from fastapi import FastAPI

import models
from database import engine

from routers import (
    health,
    auth,
    users,
    institutions,
    communities,
    internal,
    matching,
)

# ---------------------------------------------------------------------------
# DB 스키마 생성 (개발 단계용)
# ---------------------------------------------------------------------------
models.Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# FastAPI 앱 설정
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Intersection / Humane Backend (v1)",
    description="Azure Cosmos DB for PostgreSQL 기반 기억 교집합 친구 찾기 백엔드",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# 라우터 등록
# ---------------------------------------------------------------------------

# 헬스 / 루트
app.include_router(health.router)

# 인증 / 유저
app.include_router(auth.router)
app.include_router(users.router)

# 학교 검색
app.include_router(institutions.router)

# 커뮤니티
app.include_router(communities.router)

# 내부용 / 임베딩 테스트 / 재색인
app.include_router(internal.router)

# 매칭
app.include_router(matching.router)
