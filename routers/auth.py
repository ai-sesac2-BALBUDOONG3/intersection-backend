# path: routers/auth.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import crud
import models
import schemas
import security
from deps import get_db_session, get_current_user

router = APIRouter()


@router.post("/users/", response_model=schemas.User, tags=["auth"])
def signup(
    body: schemas.UserCreate,
    db: Session = Depends(get_db_session),
):
    """회원 가입 (login_id, email 중복 체크 포함)."""
    if crud.get_user_by_login_id(db, body.login_id):
        raise HTTPException(status_code=400, detail="이미 사용 중인 로그인 ID입니다.")
    if body.email and crud.get_user_by_email(db, body.email):
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")

    user = crud.create_user(db, body)
    return user


@router.post("/token", response_model=schemas.Token, tags=["auth"])
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_session),
):
    """
    로그인 & JWT 발급.
    - form_data.username 필드에 login_id가 들어온다고 가정.
    """
    user = crud.get_user_by_login_id(db, form_data.username)

    if not user or not security.verify_password(
        form_data.password, user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="로그인 ID 또는 비밀번호가 정확하지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_data = {"sub": user.login_id}
    access_token = security.create_access_token(data=access_token_data)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me", response_model=schemas.User, tags=["users"])
def read_users_me(current_user: models.User = Depends(get_current_user)):
    """현재 로그인한 사용자 정보 조회."""
    return current_user
