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

# ----------------------------------------------------
# 1. 비밀번호 해시/검증 (argon2 사용)
# ----------------------------------------------------
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    평문 비밀번호와 해시가 일치하는지 검증.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    비밀번호를 argon2 로 해시.
    """
    return pwd_context.hash(password)


# ----------------------------------------------------
# 2. JWT 설정
# ----------------------------------------------------
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1일

# 토큰 추출용 (Authorization: Bearer <token>)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def create_access_token(
    subject: str | int,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    JWT 액세스 토큰 생성.

    subject 에는 login_id(문자열) 또는 user_id(정수)를 넣을 수 있다.
    - 토큰 안에는 항상 str 로 들어간다.
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
        settings.secret_key,
        algorithm=ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[str]:
    """
    JWT 에서 sub 클레임만 꺼내서 반환.
    - 토큰이 유효하지 않으면 None
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


# ----------------------------------------------------
# 3. 현재 사용자 조회 의존성
#    - 토큰 sub 가 user_id 인 경우, login_id 인 경우 모두 처리
# ----------------------------------------------------
async def _get_user_by_id(
    db: Session,
    user_id: int,
):
    result = db.execute(
        select(models.User).where(
            models.User.id == user_id,
            models.User.is_deleted == False,
        )
    )
    return result.scalars().first()


async def _get_user_by_login_id(
    db: Session,
    login_id: str,
):
    result = db.execute(
        select(models.User).where(
            models.User.login_id == login_id,
            models.User.is_deleted == False,
        )
    )
    return result.scalars().first()


async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> models.User:
    """
    공통 인증 의존성.

    - 토큰의 sub 가 숫자면 user_id 로 먼저 시도
    - 실패하면 login_id 로 다시 시도
    - 둘 다 못 찾으면 401
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증에 실패했습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    sub = decode_access_token(token)
    if sub is None:
        raise credentials_exception

    user: Optional[models.User] = None

    # 1) sub 가 정수 형태면 user_id 로 먼저 조회
    try:
        user_id = int(sub)
    except ValueError:
        user_id = None

    if user_id is not None:
        user = await _get_user_by_id(db, user_id)

    # 2) user_id 로 못 찾았으면 login_id 로 재시도
    if user is None:
        user = await _get_user_by_login_id(db, sub)

    if user is None:
        # 토큰은 맞는데 해당 사용자가 DB 에 없는 경우
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
