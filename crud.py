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


# ========== User ==========

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
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
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not security.verify_password(password, user.hashed_password):
        return None
    return user


# ========== UserDetail ==========

def upsert_user_detail(
    db: Session,
    user: models.User,
    detail_in: schemas.UserDetailCreate,
) -> models.UserDetail:
    if user.detail:
        for field, value in detail_in.model_dump(exclude_unset=True).items():
            setattr(user.detail, field, value)
        db_detail = user.detail
    else:
        db_detail = models.UserDetail(
            owner_id=user.id,
            **detail_in.model_dump(),
        )
        db.add(db_detail)

    db.commit()
    db.refresh(db_detail)
    return db_detail


# ========== Post ==========

def get_posts(db: Session, skip: int = 0, limit: int = 100) -> list[models.Post]:
    return db.query(models.Post).offset(skip).limit(limit).all()


def create_user_post(
    db: Session,
    post: schemas.PostCreate,
    user_id: int,
) -> models.Post:
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
    return (
        db.query(models.Post)
        .filter(models.Post.owner_id == owner_id)
        .order_by(models.Post.id.desc())
        .all()
    )
