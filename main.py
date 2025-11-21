# path: main.py
"""
Intersection / Humane 로컬 백엔드 엔트리포인트
"""

from __future__ import annotations

from typing import List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import crud
import deps  # [중요] 여기서 검사 기능을 가져옵니다!
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

# [ CORS 설정 ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    로그인 -> 액세스 토큰 발급
    """
    # 1. 회원 확인
    user = crud.authenticate_user(
        db,
        email=form_data.username,
        password=form_data.password,
    )
    # 2. 실패 시 에러 발생
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. 토큰 생성
    # [주의] user.id를 문자열(str)로 변환해서 넣어야 합니다.
    access_token = security.create_access_token(data={"sub": str(user.id)})
    
    # [ ⚠️ 여기가 핵심! ] 이 줄이 없으면 500 에러(ResponseValidationError)가 납니다.
    return schemas.Token(access_token=access_token, token_type="bearer")

  # 3. 출입증(Token) 발급
    # [수정] 이메일(user.email) 대신 아이디(user.id)를 문자로 바꿔서 넣습니다.
    access_token_data = {"sub": str(user.id)} 
    access_token = security.create_access_token(data=access_token_data)

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
    current_user=Depends(deps.get_current_user), # [중요] deps를 통해 유저 확인
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


# --- [ 4. (Step 4) 추가 정보 입력 창구 ] ---
@app.post(
    "/users/me/detail",
    response_model=schemas.UserDetail,
    tags=["users"],
)
def create_my_detail(
    detail_in: schemas.UserDetailCreate,
    db: Session = Depends(get_db),
    current_user=Depends(deps.get_current_user),
):
    # [수정 완료] crud 파일의 함수 이름과 일치시킴
    return crud.create_user_detail(db=db, detail=detail_in, user_id=current_user.id)


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

@app.get("/posts", response_model=List[schemas.Post], tags=["posts"])
def read_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    posts = crud.get_posts(db, skip=skip, limit=limit)
    return posts
