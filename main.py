# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    health_router,
    auth_router,
    institutions_router,
    users_router,
    school_histories_router,
    matching_router,
    communities_router,
    anchors_router,
)

app = FastAPI(
    title="Intersection API",
    version="1.0.0",
    description="기억 교집합 기반 친구찾기 앱 Intersection 백엔드 API",
)

# ----------------------------------------------------
# CORS 설정 (Flutter Web + 나중에 모바일 앱까지 고려)
#  - 테스트용으로 모든 Origin 허용
#  - 쿠키는 쓰지 않으므로 allow_credentials=False
# ----------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # ★ 일단 전부 허용
    allow_credentials=False,      # ★ 쿠키 안 쓰니까 False로
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(institutions_router)
app.include_router(users_router)
app.include_router(school_histories_router)
app.include_router(matching_router)
app.include_router(communities_router)
app.include_router(anchors_router)


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "intersection-api"}
