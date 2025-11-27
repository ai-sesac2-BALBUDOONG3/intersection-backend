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

# CORS 설정 (Flutter / 기타 클라이언트에서 접근 가능하도록)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 필요 시 특정 도메인으로 제한 가능
    allow_credentials=True,
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
