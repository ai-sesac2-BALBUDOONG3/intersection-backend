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
# CORS 설정
#  - Flutter Web: http://localhost:포트번호 (포트는 매번 바뀌어도 허용)
#  - 나중에 실제 프론트 도메인 생기면 origins 리스트에 추가
# ----------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    # localhost:임의포트 모두 허용 (flutter run -d chrome)
    allow_origin_regex=r"^http://localhost(:\d+)?$",
    # 추후 배포된 프론트엔드 도메인 추가 예정
    allow_origins=[
        # 예시) "https://intersection-frontend.example.com",
    ],
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
