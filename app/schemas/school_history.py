# app/schemas/school_history.py

from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserSchoolHistoryBase(BaseModel):
    institution_id: Optional[int] = None
    school_name: str
    region_city: Optional[str] = None
    region_district: Optional[str] = None
    time_start_year: Optional[int] = None
    time_end_year: Optional[int] = None
    grade: Optional[str] = None
    class_name: Optional[str] = None
    homeroom_teacher_name: Optional[str] = None
    memo: Optional[str] = None


class UserSchoolHistoryCreate(UserSchoolHistoryBase):
    """
    생성용 스키마
    """
    pass


class UserSchoolHistoryRead(UserSchoolHistoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
