# path: crud.py
from typing import Optional, List

from sqlalchemy.orm import Session

import models
import schemas
import security


# ============================================================
# 1. User / Auth
# ============================================================


def get_user_by_login_id(db: Session, login_id: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.login_id == login_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user_in: schemas.UserCreate) -> models.User:
    hashed_pw = security.get_password_hash(user_in.password)

    db_user = models.User(
        login_id=user_in.login_id,
        password_hash=hashed_pw,
        real_name=user_in.real_name,
        nickname=user_in.nickname,
        email=user_in.email,
        phone=user_in.phone,
        birth_year=user_in.birth_year,
        gender=user_in.gender,
        # 기본값: status='active', signup_step=4
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # 기본 프로필 빈 값 생성
    profile = models.UserProfile(user_id=db_user.id)
    db.add(profile)
    db.commit()

    return db_user


# ============================================================
# 2. 프로필 / 학교
# ============================================================


def upsert_user_profile(
    db: Session, user_id: int, profile_in: schemas.UserProfileUpdate
) -> models.UserProfile:
    profile = db.get(models.UserProfile, user_id)
    if not profile:
        profile = models.UserProfile(user_id=user_id)

    for field, value in profile_in.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def create_user_school_anchor(
    db: Session, user_id: int, anchor_in: schemas.UserSchoolAnchorCreate
) -> models.UserSchoolAnchor:
    # 유저의 기존 primary anchor는 is_primary=false 로 변경
    if anchor_in.is_primary:
        (
            db.query(models.UserSchoolAnchor)
            .filter(
                models.UserSchoolAnchor.user_id == user_id,
                models.UserSchoolAnchor.is_primary.is_(True),
            )
            .update({"is_primary": False})
        )

    anchor = models.UserSchoolAnchor(
        user_id=user_id,
        institution_id=anchor_in.institution_id,
        school_level=anchor_in.school_level,
        entry_year=anchor_in.entry_year,
        graduation_year=anchor_in.graduation_year,
        is_primary=anchor_in.is_primary,
    )

    db.add(anchor)
    db.commit()
    db.refresh(anchor)
    return anchor


def list_user_school_anchors(
    db: Session, user_id: int
) -> List[models.UserSchoolAnchor]:
    return (
        db.query(models.UserSchoolAnchor)
        .filter(models.UserSchoolAnchor.user_id == user_id)
        .order_by(
            models.UserSchoolAnchor.is_primary.desc(),
            models.UserSchoolAnchor.entry_year,
        )
        .all()
    )


def add_user_keyword(
    db: Session, user_id: int, keyword_in: schemas.UserKeywordCreate
) -> models.UserKeyword:
    kw = models.UserKeyword(
        user_id=user_id,
        keyword=keyword_in.keyword,
        weight=keyword_in.weight,
    )
    db.add(kw)
    db.commit()
    db.refresh(kw)
    return kw


def list_user_keywords(db: Session, user_id: int) -> List[models.UserKeyword]:
    return (
        db.query(models.UserKeyword)
        .filter(models.UserKeyword.user_id == user_id)
        .order_by(models.UserKeyword.created_at.desc())
        .all()
    )


# ============================================================
# 3. 커뮤니티 / 게시글 간단 버전
# ============================================================


def create_community(
    db: Session, community_in: schemas.CommunityCreate
) -> models.Community:
    community = models.Community(
        institution_id=community_in.institution_id,
        school_level=community_in.school_level,
        entry_year=community_in.entry_year,
        residence_city=community_in.residence_city,
        residence_district=community_in.residence_district,
        name=community_in.name,
        description=community_in.description,
    )
    db.add(community)
    db.commit()
    db.refresh(community)
    return community


def create_community_post(
    db: Session, user_id: int, post_in: schemas.CommunityPostCreate
) -> models.CommunityPost:
    post = models.CommunityPost(
        community_id=post_in.community_id,
        author_user_id=user_id,
        content=post_in.content,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def list_community_posts(
    db: Session, community_id: int, limit: int = 50
) -> list[models.CommunityPost]:
    return (
        db.query(models.CommunityPost)
        .filter(models.CommunityPost.community_id == community_id)
        .order_by(models.CommunityPost.created_at.desc())
        .limit(limit)
        .all()
    )
