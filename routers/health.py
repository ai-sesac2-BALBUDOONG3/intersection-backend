# path: routers/health.py
from fastapi import APIRouter, HTTPException

from database import check_db_connection

router = APIRouter(tags=["health"])


@router.get("/health")
def health_root():
    return {"status": "ok", "message": "intersection-backend running"}


@router.get("/health/db")
def health_db():
    ok = check_db_connection()
    if not ok:
        raise HTTPException(status_code=503, detail="Database connection failed")
    return {"status": "ok", "message": "Database connection successful"}


@router.get("/", tags=["root"])
def read_root():
    return {"message": "인터섹션 백엔드 기지에 오신 것을 환영합니다!"}
