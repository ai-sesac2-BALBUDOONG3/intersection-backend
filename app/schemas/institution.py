from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class InstitutionOut(BaseModel):
    id: int
    name: str
    type: str
    region_city: Optional[str] = None
    region_district: Optional[str] = None
    address: Optional[str] = None

    class Config:
        from_attributes = True
