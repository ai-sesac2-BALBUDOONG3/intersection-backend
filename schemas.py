# path: schemas.py
from typing import Optional, List

from pydantic import BaseModel, EmailStr, ConfigDict


# ============================================================
# 1. User / Auth
# ============================================================


class UserBase(BaseModel):
    login_id: str
    real_name: str
    nickname: str
    birth_year: int
    gender: Optional[str] = None  # 'male','female','other'
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str  # 평문 비밀번호 (서버에서 해시)


class User(UserBase):
    id: int
    is_verified: bool
    status: str

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str


# ============================================================
# 2. 프로필 / 학교
# ============================================================


class UserProfileBase(BaseModel):
    residence_city: Optional[str] = None
    residence_district: Optional[str] = None
    residence_neighborhood: Optional[str] = None
    profile_visibility: Optional[str] = "friends"


class UserProfileUpdate(UserProfileBase):
    pass


class UserProfile(UserProfileBase):
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class UserSchoolAnchorBase(BaseModel):
    institution_id: int
    school_level: str  # 'elementary','middle','high'
    entry_year: int
    graduation_year: Optional[int] = None
    is_primary: Optional[bool] = True


class UserSchoolAnchorCreate(UserSchoolAnchorBase):
    pass


class UserSchoolAnchor(UserSchoolAnchorBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class UserKeywordBase(BaseModel):
    keyword: str
    weight: Optional[int] = None


class UserKeywordCreate(UserKeywordBase):
    pass


class UserKeyword(UserKeywordBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# 3. 기관(학교)
# ============================================================


class Institution(BaseModel):
    id: int
    name: str
    institution_type: str
    region_city: Optional[str] = None
    region_district: Optional[str] = None
    region_neighborhood: Optional[str] = None
    address: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# 4. 커뮤니티 / 게시글 (간단)
# ============================================================


class CommunityBase(BaseModel):
    institution_id: int
    school_level: str
    entry_year: int
    residence_city: Optional[str] = None
    residence_district: Optional[str] = None
    name: str
    description: Optional[str] = None


class CommunityCreate(CommunityBase):
    pass


class Community(CommunityBase):
    id: int
    status: str

    model_config = ConfigDict(from_attributes=True)


class CommunityPostBase(BaseModel):
    community_id: int
    content: str


class CommunityPostCreate(CommunityPostBase):
    pass


class CommunityPost(CommunityPostBase):
    id: int
    author_user_id: int

    model_config = ConfigDict(from_attributes=True)
