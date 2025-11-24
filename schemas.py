from pydantic import BaseModel
from typing import Optional, List

# ======================
# 0. 로그인 요청 모델
# ======================
class LoginRequest(BaseModel):
    email: str
    password: str


# ======================
# 1. 기본 회원가입 (Step 1~3)
# ======================
class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    birth_year: int
    gender: Optional[str] = None
    region: str
    school_name: str
    school_type: str
    admission_year: int


# ======================
# 2. 추가 정보 (Step 4)
# ======================
class UserDetailCreate(BaseModel):
    transfer_history: Optional[str] = None
    class_info: Optional[str] = None
    club_name: Optional[str] = None
    nickname: Optional[str] = None
    memory_keywords: Optional[str] = None


class UserDetail(UserDetailCreate):
    id: int
    owner_id: int

    class Config:
        from_attributes = True


# ======================
# 3. 회원 정보 (조회용)
# ======================
class User(BaseModel):
    id: int
    email: str
    name: str
    birth_year: int
    gender: Optional[str]
    region: str
    school_name: str
    school_type: str
    admission_year: int
    is_active: bool

    # 추가 정보 포함
    detail: Optional[UserDetail] = None

    class Config:
        from_attributes = True


# ======================
# 4. 토큰
# ======================
class Token(BaseModel):
    access_token: str
    token_type: str


# ======================
# 5. 게시물
# ======================
class PostCreate(BaseModel):
    title: str
    content: str


class Post(BaseModel):
    id: int
    title: str
    content: str
    owner_id: int

    class Config:
        from_attributes = True
