from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    id: int
    login_id: str
    real_name: str
    nickname: str
    email: Optional[str] = None
    birth_year: Optional[int] = None
    gender: Optional[str] = None
    status: str
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)


class UserRead(UserBase):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserRegisterRequest(BaseModel):
    """
    회원가입 요청 바디

    - login_id: Intersection에서 사용하는 로그인용 ID (이메일/닉네임/임의 ID 모두 가능)
    - password: 평문 비밀번호 (서버에서 해시 처리)
    """
    login_id: str
    password: str
    real_name: str
    nickname: str
    email: Optional[str] = None


class UserLoginRequest(BaseModel):
    """
    로그인 요청 바디

    Flutter에서는 "로그인 ID" 입력값을 login_id 필드에 담아 전송.
    """
    login_id: str
    password: str
