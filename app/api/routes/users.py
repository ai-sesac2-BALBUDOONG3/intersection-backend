# app/api/routes/users.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api import deps
from app.db import models
from app.schemas.user import UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut, summary="내 프로필 조회")
def get_me(
    current_user=Depends(deps.get_current_user),
) -> UserOut:
    """
    현재 로그인한 유저의 프로필을 반환.
    - JWT 토큰에서 login_id를 복원 (deps.get_current_user)
    - 탈퇴/삭제 상태가 아닌 유저만 허용
    """
    return current_user


@router.patch("/me", response_model=UserOut, summary="내 프로필 수정")
def update_me(
    payload: UserUpdate,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
) -> UserOut:
    """
    현재 로그인한 유저의 닉네임/실명/이메일을 수정.
    - 비어 있는 문자열은 무시 (기존 값 유지)
    """
    if payload.nickname is not None:
        nickname = payload.nickname.strip()
        if nickname:
            current_user.nickname = nickname

    if payload.real_name is not None:
        real_name = payload.real_name.strip()
        current_user.real_name = real_name or current_user.real_name

    if payload.email is not None:
        current_user.email = payload.email

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get(
    "/{user_id}",
    response_model=UserOut,
    summary="특정 유저 프로필 조회",
)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user=Depends(deps.get_current_user),
) -> UserOut:
    """
    ID로 다른 유저의 공개 프로필 조회.
    - soft delete 된 유저(is_deleted = true)는 조회 불가.
    """
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

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다.",
        )

    return user
