from pydantic import BaseModel
from typing import Optional # '선택 사항'을 위해 필요

# --- 1. '회원가입 신청서' (입력용) ---
# 손님이 회원가입할 때 딱 이 정보만 받습니다.
class UserCreate(BaseModel):
    email: str
    password: str # '원본' 비밀번호를 받습니다.

    name : str
    birth_year : int
    gender : Optional[str] = None  # 선택 사항


    region: str
    school_name : str
    school_type : str
    admission_year : int 

# --- 2. '발급용 회원증' (출력용) ---
# 회원가입이 성공하거나, 정보를 조회할 때 이 양식으로 보여줍니다.
# [ ⚠️ 보안! ] 절대로 'hashed_password'는 보여주지 않습니다!
class User(BaseModel):
    id: int
    email: str
    region: str
    school_name: str
    is_active: bool

    # [ 💡 Tip! ]
    # 이 설정은 SQLAlchemy '리모컨'이 '창고'에서 데이터를 꺼낸 뒤,
    # 이 '회원증' 양식에 맞게 자동으로 변환해 주라고 알려주는 스위치입니다.
    class Config:
        from_attributes = True 
        # (이전 버전에서는 orm_mode = True 였습니다)

    
# --- 3. '출입증' 양식 ---
# 로그인을 할 때 이 '출입증' 양식으로 토큰을 발급합니다.
class Token(BaseModel):
    access_token: str # '출입증' (jwt 토큰)
    token_type: str # '출입증' 종류 (항상 "bearer" 입니다)


#게시물 신청서 (입력용)
class PostCreate(BaseModel):
    title: str
    content: str

#게시물 양식 (출력용)
class Post(BaseModel):
    id: int
    title: str
    content: str
    owner_id: int # 게시물 소유자 ID

    class Config:
        from_attributes = True

