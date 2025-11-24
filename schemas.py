from pydantic import BaseModel
from typing import Optional, List

# [기본 유저 생성]
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

# [유저 상세 정보]
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
        orm_mode = True

# [유저 정보 보여주기]
# [schemas.py 파일 중간쯤]
# "유저 정보 보여주기" 부분을 찾아서 아래 내용으로 덮어쓰세요.

class User(BaseModel):
    id: int
    email: str
    name: str
    school_name: str
    
    # ▼▼▼ [누락되었던 친구들 추가!] ▼▼▼
    birth_year: int        # 앱이 이 숫자를 기다리고 있었음!
    admission_year: int    # 얘도 앱이 기다리고 있었음!
    region: str
    school_type: str
    gender: Optional[str] = None

    detail: Optional[UserDetail] = None

    class Config:
        orm_mode = True

# [로그인 데이터]
class LoginRequest(BaseModel):
    email: str
    password: str

# [토큰]
class Token(BaseModel):
    access_token: str
    token_type: str

# [게시글 생성]
class PostCreate(BaseModel):
    title: str
    content: str

# [게시글 보여주기]
class Post(BaseModel):
    id: int
    title: str
    content: str
    owner_id: int
    class Config:
        orm_mode = True

# --- [새로 추가된 부분] ---

# 1. 게시글 수정용 양식
class PostUpdate(BaseModel):
    title: str
    content: str

# 2. 댓글 작성용 양식
class CommentCreate(BaseModel):
    content: str

# 3. 댓글 보여주기용 양식
class Comment(BaseModel):
    id: int
    content: str
    owner_id: int
    post_id: int
    class Config:
        orm_mode = True