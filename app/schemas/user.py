# app/schemas/user.py

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """
    공통으로 사용하는 기본 유저 정보 스키마.
    (DB models.User와 매핑되는 필드들)
    """
    login_id: str = Field(..., description="로그인용 ID (고유값)")
    nickname: str = Field(..., description="표시용 닉네임")
    real_name: Optional[str] = Field(None, description="실명")
    email: Optional[EmailStr] = Field(None, description="이메일")
    status: str = Field("active", description="계정 상태 (active/suspended/deleted)")


class UserOut(BaseModel):
    """
    클라이언트로 내려보내는 유저 정보 (민감한 정보 제외).
    """
    id: int = Field(..., description="유저 ID (PK)")
    login_id: str = Field(..., description="로그인용 ID")
    nickname: str = Field(..., description="표시용 닉네임")
    real_name: Optional[str] = Field(None, description="실명")
    email: Optional[EmailStr] = Field(None, description="이메일")
    status: str = Field(..., description="계정 상태")
    created_at: datetime = Field(..., description="계정 생성 시각")
    updated_at: datetime = Field(..., description="마지막 수정 시각")

    class Config:
        from_attributes = True  # SQLAlchemy 모델에서 바로 변환 가능


class UserUpdate(BaseModel):
    """
    내 정보 수정 시 사용할 스키마 (/users/me PATCH).
    """
    nickname: Optional[str] = Field(None, description="변경할 닉네임")
    real_name: Optional[str] = Field(None, description="변경할 실명")
    email: Optional[EmailStr] = Field(None, description="변경할 이메일")


class UserListItem(UserOut):
    """
    필요하면 유저 리스트 응답용으로 확장할 수 있는 타입.
    현재는 UserOut과 동일.
    """
    pass
