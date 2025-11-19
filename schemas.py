from pydantic import BaseModel
from typing import Optional

# --- [ 1. (Step 1~3) 기본 회원가입 신청서 ] ---
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

# --- [ 2. (Step 4) 추가 정보 신청서 ] ---
class UserDetailCreate(BaseModel):
    transfer_history: Optional[str] = None
    class_info: Optional[str] = None
    club_name: Optional[str] = None
    nickname: Optional[str] = None
    memory_keywords: Optional[str] = None

# --- [ 3. 추가 정보 확인증 ] ---
class UserDetail(UserDetailCreate):
    id: int
    owner_id: int
    class Config:
        from_attributes = True

# --- [ 4. 회원증 (기본 정보) ] ---
class User(BaseModel):
    id: int
    email: str
    name: str
    region: str
    school_name: str
    is_active: bool
    # (나중에 추가 정보도 같이 보여줄 수 있게 설정 가능)
    detail: Optional[UserDetail] = None 

    class Config:
        from_attributes = True

# --- [ 5. 기타 (토큰, 게시물 등) ] ---
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
    class Config:
        from_attributes = True