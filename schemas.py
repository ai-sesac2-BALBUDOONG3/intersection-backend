from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime # 👈 시간 정보를 사용하기 위해 추가

# --- [ User (사용자) 관련 스키마 ] ---

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
    # 프로필 사진은 등록 후 별도 업데이트로 처리한다고 가정하고, create 시에는 제외

# [유저 상세 정보 생성]
class UserDetailCreate(BaseModel):
    transfer_history: Optional[str] = None
    class_info: Optional[str] = None
    club_name: Optional[str] = None
    nickname: Optional[str] = None
    memory_keywords: Optional[str] = None

# [유저 상세 정보 보여주기]
class UserDetail(UserDetailCreate):
    id: int
    owner_id: int
    class Config:
        from_attributes = True # FastAPI 2.0+ 버전에서 orm_mode=True 대신 사용

# [유저 정보 보여주기]
class User(BaseModel):
    id: int
    email: str
    name: str
    school_name: str
    
    birth_year: int
    admission_year: int
    region: str
    school_type: str
    gender: Optional[str] = None
    profile_image: Optional[str] = None # 👈 models.py에 추가되었으므로 포함

    detail: Optional[UserDetail] = None
    # posts: List["Post"] = [] # 게시글 목록은 순환 참조를 피하기 위해 보통 생략

    class Config:
        from_attributes = True

# --- [ 인증 관련 스키마 ] ---

# [로그인 데이터]
class LoginRequest(BaseModel):
    email: str
    password: str

# [토큰]
class Token(BaseModel):
    access_token: str
    token_type: str

# --- [ Comment (댓글) 관련 스키마 ] ---

# 2. 댓글 작성용 양식
class CommentCreate(BaseModel):
    content: str

# 3. 댓글 보여주기용 양식
class Comment(BaseModel):
    id: int
    content: str
    owner_id: int
    post_id: int
    created_at: datetime # 👈 models.py에 맞춰 시간 정보 추가
    
    # ⭐️ 관계 필드 (선택 사항: 작성자 정보 포함)
    # owner: User # 만약 댓글 조회 시 작성자 정보까지 보여주고 싶다면 추가 (순환 참조 주의)
    
    class Config:
        from_attributes = True

# --- [ Post (게시글) 관련 스키마 ] ---

# [게시글 생성]
class PostCreate(BaseModel):
    title: str
    content: str

# 1. 게시글 수정용 양식 (수정 시 필드를 모두 입력하게 함)
class PostUpdate(BaseModel):
    title: str
    content: str

# [게시글 보여주기]
class Post(BaseModel):
    id: int
    title: str
    content: str
    owner_id: int
    
    # ⭐️ models.py에 맞춰 시간 정보 추가
    created_at: datetime
    updated_at: datetime
    
    # ⭐️ models.py에 맞춰 댓글 목록 포함 (List['Comment']를 사용해 순환 참조 처리)
    comments: List[Comment] = [] 
    
    # ⭐️ 관계 필드 (선택 사항: 작성자 정보 포함)
    # owner: User 
    
    class Config:
        from_attributes = True

# --- [ Friend (친구) 관련 스키마 ] ---

# 친구 요청을 위한 기본 양식 (user_id는 current_user에서 가져오므로 friend_id만 필요할 수 있음)
class FriendCreate(BaseModel):
    friend_id: int # 친구 추가 대상 ID

# 친구 관계를 보여주기 위한 양식
class Friend(BaseModel):
    # models.py에서 user_id와 friend_id가 기본 키 역할을 합니다.
    user_id: int 
    friend_id: int
    created_at: datetime # 👈 models.py에 맞춰 친구 맺은 시간 추가

    class Config:
        from_attributes = True