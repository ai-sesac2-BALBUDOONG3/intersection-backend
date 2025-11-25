# app/api/routes/health.py

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get("", summary="Health check")
def health_check(db: Session = Depends(get_db)):
    """
    애플리케이션 및 DB 헬스체크.

    - status: 전체 앱 상태
    - db: DB 연결 결과
    """
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ok",
            "db": "ok",
        }
    except Exception as e:
        # 운영 시에는 로깅 필요 (# TODO: logging 연동)
        return {
            "status": "error",
            "db": "error",
            "detail": str(e),
        }
