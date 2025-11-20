# path: schemas.py
"""
Pydantic 스키마

- User / UserDetail
- Institution
- Memory / MemoryPersonHint / MemoryTag / MemoryTagLink
- MatchSession / MatchCandidate
- BridgeDM
- Token / Post
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


# ========= User =========

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    birth_year: int
    gender: Optional[str] = None
    region: str
    school_name: str
    school_type: str
    admission_year: int


class UserBase(BaseModel):
    id: int
    email: EmailStr
    name: str
    region: str
    school_name: str
    is_active: bool

    class Config:
        from_attributes = True


class UserDetailCreate(BaseModel):
    transfer_history: Optional[str] = None
    class_info: Optional[str] = None
    club_name: Optional[str] = None
    nickname: Optional[str] = None
    memory_keywords: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None


class UserDetail(BaseModel):
    id: int
    transfer_history: Optional[str] = None
    class_info: Optional[str] = None
    club_name: Optional[str] = None
    nickname: Optional[str] = None
    memory_keywords: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    owner_id: int

    class Config:
        from_attributes = True


class User(UserBase):
    detail: Optional[UserDetail] = None

    class Config:
        from_attributes = True


# ========= Institution =========

class InstitutionBase(BaseModel):
    name: str
    type: Optional[str] = None
    region_city: Optional[str] = None
    region_district: Optional[str] = None
    address: Optional[str] = None
    external_code: Optional[str] = None


class InstitutionCreate(InstitutionBase):
    pass


class Institution(InstitutionBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========= Memory & Hints & Tags =========

class MemoryPersonHintBase(BaseModel):
    person_name: Optional[str] = None
    person_type: Optional[str] = None
    nickname: Optional[str] = None
    description: Optional[str] = None


class MemoryPersonHintCreate(MemoryPersonHintBase):
    pass


class MemoryPersonHint(MemoryPersonHintBase):
    id: int
    memory_id: int

    class Config:
        from_attributes = True


class MemoryBase(BaseModel):
    title: str
    description: Optional[str] = None
    time_start_year: Optional[int] = None
    time_end_year: Optional[int] = None
    region_city: Optional[str] = None
    region_district: Optional[str] = None
    institution_id: Optional[int] = None
    custom_school_name: Optional[str] = None
    is_public: bool = True


class MemoryCreate(MemoryBase):
    pass


class Memory(MemoryBase):
    id: int
    owner_id: int
    status: str
    created_at: datetime
    updated_at: datetime
    people_hints: List[MemoryPersonHint] = []

    class Config:
        from_attributes = True


class MemoryTagBase(BaseModel):
    name: str
    category: Optional[str] = None


class MemoryTagCreate(MemoryTagBase):
    pass


class MemoryTag(MemoryTagBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MemoryTagLink(BaseModel):
    id: int
    memory_id: int
    tag_id: int

    class Config:
        from_attributes = True


# ========= Matching =========

class MatchSessionBase(BaseModel):
    query_text: Optional[str] = None


class MatchSessionCreate(MatchSessionBase):
    pass


class MatchSession(MatchSessionBase):
    id: int
    requester_user_id: int
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MatchCandidateBase(BaseModel):
    session_id: int
    candidate_user_id: int
    matched_memory_id: Optional[int] = None
    score: Optional[float] = None
    rank: Optional[int] = None
    status: str = "suggested"


class MatchCandidateCreate(MatchCandidateBase):
    pass


class MatchCandidate(BaseModel):
    id: int
    session_id: int
    candidate_user_id: int
    matched_memory_id: Optional[int] = None
    score: Optional[float] = None
    rank: Optional[int] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ========= Bridge DM =========

class BridgeDMBase(BaseModel):
    target_user_id: int
    match_session_id: Optional[int] = None
    initial_message: Optional[str] = None


class BridgeDMCreate(BridgeDMBase):
    pass


class BridgeDM(BaseModel):
    id: int
    requester_user_id: int
    target_user_id: int
    match_session_id: Optional[int] = None
    initial_message: Optional[str] = None
    status: str
    created_at: datetime
    responded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========= Auth & Post =========

class Token(BaseModel):
    access_token: str
    token_type: str


class PostCreate(BaseModel):
    title: str
    content: str


class Post(BaseModel):
    id: int
    title: str
    content: str
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True
