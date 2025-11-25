# app/schemas/matching.py

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class MatchCandidateRead(BaseModel):
    user_id: int
    nickname: str
    real_name: str
    email: Optional[EmailStr] = None

    school_history_id: int
    school_name: str
    region_city: Optional[str] = None
    region_district: Optional[str] = None
    time_start_year: Optional[int] = None
    time_end_year: Optional[int] = None
    grade: Optional[str] = None
    class_name: Optional[str] = None
    homeroom_teacher_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MatchCandidateWithExplanationRead(MatchCandidateRead):
    explanation: str
