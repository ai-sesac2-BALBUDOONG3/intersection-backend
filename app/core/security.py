# app/core/security.py

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.db import models

# =====================================
# 비밀번호 해시/검증용 컨텍스트
#  - bcrypt 대신 argon2만 사용
# =====================================
pwd_context = CryptContext(
    schemes=["argon2"],
    default="argon2",
    deprecated="auto",
)

# JWT 설정
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1일

# 토큰 추출용 (Authorization: Bearer <token>)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    평문 비밀번호와 저장된 해시를 비교 (argon2).
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    평문 비밀번호를 argon2 해시로 변환.
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: str | int,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    JWT 액세스 토큰 생성.
    subject에는 login_id 또는 user_id 등 식별자를 문자열/정수 형태로 넣는다.
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {
        "sub": str(subject),
        "exp": expire,
    }
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,  # app.core.config.settings.secret_key 사용
        algorithm=ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[str]:
    """
    JWT 액세스 토큰에서 sub 클레임을 꺼내는 함수.
    - 유효하지 않은 토큰이거나 sub가 없으면 None 반환.
    - sub가 있으면 문자열로 반환 (login_id든 user_id든 토큰 생성 시 넣은 값 그대로 사용).
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
        )
    except JWTError:
        return None

    sub = payload.get("sub")
    if sub is None:
        return None

    return str(sub)


async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> models.User:
    """
    토큰의 sub를 user_id(int)로 간주하는 의존성.
    현재 프로젝트에서는 app.api.deps.get_current_user가
    login_id 기반 인증에 사용되고 있고,
    이 함수는 필요 시 user_id 기반 인증 엔드포인트에서 사용할 수 있다.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
        )
        sub = payload.get("sub")
        if sub is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    try:
        user_id = int(sub)
    except ValueError:
        raise credentials_exception

    result = db.execute(
        select(models.User).where(
            models.User.id == user_id,
            models.User.is_deleted == False,
        )
    )
    user = result.scalars().first()

    if user is None:
        raise credentials_exception

    return user
