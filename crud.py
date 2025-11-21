# path: crud.py
"""
DB CRUD 로직
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

import models
import schemas
import security


# ========== User (기본 회원가입 & 조회) ==========

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """이메일로 회원 찾기"""
    return db.query(models.User).filter(models.User.email == email).first()


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """ID로 회원 찾기"""
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """신규 회원 등록 (Step 1~3 필수 정보)"""
    hashed_password = security.get_password_hash(user.password)

    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        name=user.name,
        birth_year=user.birth_year,
        gender=user.gender,
        region=user.region,
        school_name=user.school_name,
        school_type=user.school_type,
        admission_year=user.admission_year,
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    """로그인 인증 (이메일/비번 확인)"""
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not security.verify_password(password, user.hashed_password):
        return None
    return user


# ========== UserDetail (추가 정보 입력) ==========

def create_user_detail(
    db: Session, 
    detail: schemas.UserDetailCreate, 
    user_id: int
) -> models.UserDetail:
    """
    추가 정보 등록 및 수정 (Step 4)
    - 이미 정보가 있으면 수정(Update)
    - 없으면 새로 생성(Create)
    """
    # 1. 기존 정보가 있는지 확인
    db_detail = db.query(models.UserDetail).filter(models.UserDetail.owner_id == user_id).first()
    
    # 2. 입력 데이터를 딕셔너리로 변환 (Pydantic V2 문법)
    detail_data = detail.model_dump(exclude_unset=True)

    if db_detail:
        # [수정 모드] 기존 정보 업데이트
        for key, value in detail_data.items():
            setattr(db_detail, key, value)
    else:
        # [신규 등록 모드] 새로 만들기
        db_detail = models.UserDetail(**detail_data, owner_id=user_id)
        db.add(db_detail)

    db.commit()
    db.refresh(db_detail)
    return db_detail


# ========== Post (게시판) ==========

def get_posts(db: Session, skip: int = 0, limit: int = 100) -> list[models.Post]:
    """전체 게시물 목록 조회"""
    return db.query(models.Post).offset(skip).limit(limit).all()


def create_user_post(
    db: Session,
    post: schemas.PostCreate,
    user_id: int,
) -> models.Post:
    """게시물 작성"""
    db_post = models.Post(
        title=post.title,
        content=post.content,
        owner_id=user_id,
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def get_posts_by_owner(db: Session, owner_id: int) -> list[models.Post]:
    """특정 사용자가 쓴 글 조회"""
    return (
        db.query(models.Post)
        .filter(models.Post.owner_id == owner_id)
        .order_by(models.Post.id.desc())
        .all()
    )