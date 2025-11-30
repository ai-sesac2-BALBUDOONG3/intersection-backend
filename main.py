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
    friends_router,  # ★ 신규 추가
)

# ----------------------------------------------------
# FastAPI 앱 생성
# ----------------------------------------------------
app = FastAPI(
    title="Intersection API",
    version="1.0.0",
    description="기억 교집합 기반 친구찾기 앱 Intersection 백엔드 API",
)

# ----------------------------------------------------
# CORS 설정
#
#  - flutter run -d chrome → http://localhost:랜덤포트
#  - 나중에 웹 배포 시에는 실제 FE 도메인을 origins 에 추가하면 됨.
#
#  - App Service 자체 CORS는 끄고(FastAPI에서만 CORS 처리),
#    여기서 Origin / Method / Header 를 모두 허용한다.
# ----------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    # 로컬 개발용: http://localhost:아무 포트
    allow_origin_regex=r"^http://localhost(:\d+)?$",
    # 필요하면 나중에 실제 프론트엔드 도메인도 허용:
    # allow_origins=["https://intersection-frontend-xxx.azurewebsites.net"],
    allow_credentials=True,
    allow_methods=["*"],   # GET, POST, OPTIONS, PUT, DELETE 등 전부
    allow_headers=["*"],   # Content-Type, Authorization 등 전부
)

# ----------------------------------------------------
# 라우터 등록
# ----------------------------------------------------
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(institutions_router)
app.include_router(users_router)
app.include_router(school_histories_router)
app.include_router(matching_router)
app.include_router(communities_router)
app.include_router(anchors_router)
app.include_router(friends_router)  # ★ 신규 추가


@app.get("/", tags=["health"])
def root():
    # ★ 이 값을 보고 실제 배포 버전인지 확인할 거야
    return {
        "status": "ok",
        "service": "intersection-api",
        "cors_debug_version": "2025-11-27-v1",
    }
