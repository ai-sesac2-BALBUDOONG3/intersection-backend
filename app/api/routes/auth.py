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
from app.db.models import User  # ✅ 단일 모델 소스
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
    """
    회원가입

    - login_id 중복 체크
    - 비밀번호 해시 저장
    - user_profiles 기본 레코드 1개 자동 생성 시도
    """
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
    try:
        db.execute(
            text(
                "INSERT INTO user_profiles (user_id) VALUES (:user_id)"
            ),
            {"user_id": user.id},
        )
    except Exception:
        # TODO: 운영 환경에서는 로깅 필요
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
    """
    로그인

    - login_id 기준으로 유저 조회
    - soft delete / status 체크
    - 비밀번호 검증 후 JWT 토큰 발급
    """
    user = (
        db.query(User)
        .filter(
            User.login_id == payload.login_id,
            User.is_deleted == False,  # noqa: E712
            User.status == "active",
        )
        .first()
    )

    if not user or not verify_password(payload.password, user.password_hash):
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
    """
    현재 토큰 기준 내 정보 조회
    """
    return UserRead.model_validate(current_user)
