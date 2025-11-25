# app/api/routes/auth.py

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    Token,
    UserLoginRequest,
    UserRead,
    UserRegisterRequest,
)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="회원 가입",
)
def register_user(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    # login_id 중복 체크
    existing = (
        db.query(User)
        .filter(User.login_id == payload.login_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="로그인 ID가 이미 사용 중입니다.",
        )

    # User 생성
    user = User(
        login_id=payload.login_id,
        password_hash=get_password_hash(payload.password),
        real_name=payload.real_name,
        nickname=payload.nickname,
        email=payload.email,
    )
    db.add(user)
    db.flush()  # user.id 확보

    # user_profiles 기본 레코드 생성 시도
    # ⚠️ 가정: user_profiles(user_id)만 NOT NULL이고 나머지는 기본값/NULL 허용
    try:
        db.execute(
            text(
                "INSERT INTO user_profiles (user_id) VALUES (:user_id)"
            ),
            {"user_id": user.id},
        )
    except Exception:
        # TODO: 운영 시에는 로깅으로 남기고, 여기서 예외는 잠시 무시
        pass

    db.commit()
    db.refresh(user)

    return UserRead.model_validate(user)


@router.post(
    "/login",
    response_model=Token,
    summary="로그인 후 액세스 토큰 발급",
)
def login(
    payload: UserLoginRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.login_id == payload.login_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인 ID 또는 비밀번호가 올바르지 않습니다.",
        )

    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인 ID 또는 비밀번호가 올바르지 않습니다.",
        )

    access_token_expires = timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token = create_access_token(
        subject=user.id,
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserRead,
    summary="내 정보 조회 (토큰 필요)",
)
async def read_me(
    current_user: User = Depends(get_current_user),
):
    return UserRead.model_validate(current_user)
