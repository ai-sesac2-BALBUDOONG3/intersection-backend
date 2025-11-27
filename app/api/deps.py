# app/api/deps.py
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.db import models

# 실제 로그인 엔드포인트에 맞춰 tokenUrl 정리 (/auth/login)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """
    공통 인증 의존성.

    - JWT 토큰의 sub 값을 꺼낸다.
    - sub 가 숫자이면 user.id 기준으로 먼저 조회
    - 못 찾으면 login_id 기준으로 다시 조회
    - 그래도 없으면 401 (사용자를 찾을 수 없습니다.)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보가 유효하지 않습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        raise credentials_exception

    # JWT에서 sub 복원 (user_id 또는 login_id)
    sub = decode_access_token(token)
    if not sub:
        raise credentials_exception

    user = None

    # 1) sub 가 정수 형태면 user.id 로 조회
    try:
        user_id = int(sub)
    except ValueError:
        user_id = None

    if user_id is not None:
        user = (
            db.execute(
                select(models.User).where(
                    models.User.id == user_id,
                    models.User.is_deleted == False,
                )
            )
            .scalars()
            .first()
        )

    # 2) user.id 기준으로 못 찾았으면 login_id 기준으로 재시도
    if user is None:
        user = (
            db.execute(
                select(models.User).where(
                    models.User.login_id == sub,
                    models.User.is_deleted == False,
                )
            )
            .scalars()
            .first()
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
