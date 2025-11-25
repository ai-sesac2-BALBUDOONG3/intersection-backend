# app/api/routes/institutions.py
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db import models
from app.schemas.institution import InstitutionOut

router = APIRouter(prefix="/institutions", tags=["institutions"])


@router.get("/search", response_model=list[InstitutionOut])
def search_institutions(
    q: str = Query(""),
    city: str | None = Query(None),
    district: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(models.Institution).where(models.Institution.status == "active")

    if q:
        like = f"%{q}%"
        stmt = stmt.where(models.Institution.name.ilike(like))
    if city:
        stmt = stmt.where(models.Institution.region_city == city)
    if district:
        stmt = stmt.where(models.Institution.region_district == district)

    stmt = stmt.order_by(models.Institution.name).limit(limit)
    rows = db.execute(stmt).scalars().all()
    return rows
