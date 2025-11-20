# path: routers/institutions.py
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import models
import schemas
from deps import get_db_session

router = APIRouter(tags=["institutions"])


@router.get(
    "/institutions/search",
    response_model=List[schemas.Institution],
)
def search_institutions(
    q: Optional[str] = Query(
        None,
        description="학교명 검색어 (부분 일치)",
    ),
    city: Optional[str] = Query(None, description="시/도 (region_city)"),
    district: Optional[str] = Query(None, description="구/군 (region_district)"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db_session),
):
    """
    학교 마스터 검색.
    - q: 이름 부분일치
    - city/district: 지역 필터
    """
    query = db.query(models.Institution).filter(models.Institution.is_active.is_(True))

    if q:
        like = f"%{q}%"
        query = query.filter(models.Institution.name.ilike(like))

    if city:
        query = query.filter(models.Institution.region_city == city)
    if district:
        query = query.filter(models.Institution.region_district == district)

    institutions = query.order_by(models.Institution.name).limit(limit).all()
    return institutions
