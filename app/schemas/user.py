# app/schemas/auth.py

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class UserRead(BaseModel):
    id: int
    login_id: str
    nickname: str
    real_name: str
    email: Optional[EmailStr] = None

    model_config = ConfigDict(from_attributes=True)


class UserRegisterRequest(BaseModel):
    login_id: str
    password: str
    nickname: str
    real_name: str
    email: Optional[EmailStr] = None


class UserLoginRequest(BaseModel):
    login_id: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
