# path: deps.py
"""
FastAPI 의존성:
- DB 세션
- 현재 로그인 유저
"""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

import crud
import security
from database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_db_session():
    yield from get_db()


def get_current_user(
    db: Session = Depends(get_db_session),
    token: str = Depends(oauth2_scheme),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = security.decode_access_token(token)
        user_id: Optional[int] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except ValueError:
        raise credentials_exception

    user = crud.get_user(db, user_id=user_id)
    if user is None:
        raise credentials_exception
    return user
