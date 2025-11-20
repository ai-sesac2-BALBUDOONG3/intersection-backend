# path: main.py
"""
Intersection / Humane 로컬 백엔드 엔트리포인트

- /health, /health/db
- /token (로그인)
- /users (회원 가입, 조회)
- /users/me, /users/me/detail
- /posts/me
"""

from __future__ import annotations

from typing import List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import crud
import deps
import models
import schemas
import security
from database import Base, check_db_health, engine, get_db

# 로컬 개발 편의용: 앱 시작 시 테이블 없으면 생성
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Intersection Backend (Local)",
    version="0.1.0",
)


# ========== Health ==========

@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


@app.get("/health/db", tags=["health"])
def health_db():
    return check_db_health()


# ========== Auth ==========

@app.post("/token", response_model=schemas.Token, tags=["auth"])
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    이메일/비밀번호 기반 로그인 → 액세스 토큰 발급.
    - form_data.username 에 email 넣기
    """
    user = crud.authenticate_user(
        db,
        email=form_data.username,
        password=form_data.password,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = security.create_access_token(data={"sub": user.id})
    return schemas.Token(access_token=access_token, token_type="bearer")


# ========== Users ==========

@app.post("/users", response_model=schemas.User, status_code=201, tags=["users"])
def create_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = crud.get_user_by_email(db, email=user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered.",
        )
    user = crud.create_user(db, user=user_in)
    return user


@app.get("/users/me", response_model=schemas.User, tags=["users"])
def read_current_user(
    current_user=Depends(deps.get_current_user),
):
    return current_user


@app.get("/users/{user_id}", response_model=schemas.User, tags=["users"])
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user


@app.put(
    "/users/me/detail",
    response_model=schemas.UserDetail,
    tags=["users"],
)
def upsert_my_detail(
    detail_in: schemas.UserDetailCreate,
    db: Session = Depends(get_db),
    current_user=Depends(deps.get_current_user),
):
    detail = crud.upsert_user_detail(db, user=current_user, detail_in=detail_in)
    return detail


@app.get(
    "/users/{user_id}/detail",
    response_model=schemas.UserDetail,
    tags=["users"],
)
def read_user_detail(user_id: int, db: Session = Depends(get_db)):
    user = crud.get_user(db, user_id=user_id)
    if not user or not user.detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User detail not found.",
        )
    return user.detail


# ========== Posts ==========

@app.post(
    "/posts",
    response_model=schemas.Post,
    status_code=201,
    tags=["posts"],
)
def create_my_post(
    post_in: schemas.PostCreate,
    db: Session = Depends(get_db),
    current_user=Depends(deps.get_current_user),
):
    post = crud.create_user_post(db, post=post_in, user_id=current_user.id)
    return post


@app.get(
    "/posts/me",
    response_model=List[schemas.Post],
    tags=["posts"],
)
def read_my_posts(
    db: Session = Depends(get_db),
    current_user=Depends(deps.get_current_user),
):
    posts = crud.get_posts_by_owner(db, owner_id=current_user.id)
    return posts
