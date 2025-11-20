# path: deps.py
from typing import Generator

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

import crud
import models
import security
from database import get_db

# OAuth2: /token 엔드포인트를 통해 토큰 발급
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI 의존성 주입용 DB 세션.

    - 필요한 곳에서 Depends(get_db_session) 으로 사용
    - 내부에서는 기존 database.get_db 제너레이터를 그대로 사용
    """
    yield from get_db()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db_session),
) -> models.User:
    """
    JWT 토큰을 검증하고 현재 로그인 유저를 반환.
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="출입증(Token)이 유효하지 않습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = security.verify_token(token, credentials_exception)
    login_id: str = payload.get("sub")

    user = crud.get_user_by_login_id(db, login_id=login_id)
    if user is None:
        raise credentials_exception

    return user
