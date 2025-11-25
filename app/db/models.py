# app/db/models.py
from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.session import Base


# =========================
# 공통 Mixin
# =========================

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow
    )


# =========================
# 1. 매칭 핵심 도메인
# =========================

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    login_id: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)

    real_name: Mapped[str] = mapped_column(Text, nullable=False)
    nickname: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(Text, unique=True)

    birth_year: Mapped[Optional[int]] = mapped_column(SmallInteger)
    gender: Mapped[Optional[str]] = mapped_column(String(10))

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    profile: Mapped["UserProfile"] = relationship(
        "UserProfile", back_populates="user", uselist=False
    )
    school_histories: Mapped[List["UserSchoolHistory"]] = relationship(
        "UserSchoolHistory", back_populates="user"
    )
    school_anchors: Mapped[List["UserSchoolAnchor"]] = relationship(
        "UserSchoolAnchor", back_populates="user"
    )

    keywords: Mapped[List["UserKeyword"]] = relationship(
        "UserKeyword", back_populates="user"
    )

    # friendships, communities 등은 필요한 곳만 relationship 사용


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    bio: Mapped[Optional[str]] = mapped_column(Text)
    profile_image_url: Mapped[Optional[str]] = mapped_column(Text)

    region_country: Mapped[Optional[str]] = mapped_column(Text)
    region_city: Mapped[Optional[str]] = mapped_column(Text)
    region_district: Mapped[Optional[str]] = mapped_column(Text)

    is_searchable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    allow_friend_request: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped[User] = relationship("User", back_populates="profile")


class Institution(Base, TimestampMixin):
    __tablename__ = "institutions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    external_id: Mapped[Optional[str]] = mapped_column(Text, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="school")
    region_country: Mapped[Optional[str]] = mapped_column(Text)
    region_city: Mapped[Optional[str]] = mapped_column(Text)
    region_district: Mapped[Optional[str]] = mapped_column(Text)
    address: Mapped[Optional[str]] = mapped_column(Text)
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(9, 6))

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    school_histories: Mapped[List["UserSchoolHistory"]] = relationship(
        "UserSchoolHistory", back_populates="institution"
    )
    school_anchors: Mapped[List["UserSchoolAnchor"]] = relationship(
        "UserSchoolAnchor", back_populates="institution"
    )


class UserSchoolHistory(Base, TimestampMixin):
    __tablename__ = "user_school_histories"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    institution_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("institutions.id"), index=True
    )

    school_name_snapshot: Mapped[Optional[str]] = mapped_column(Text)
    grade: Mapped[Optional[int]] = mapped_column(SmallInteger)
    class_name: Mapped[Optional[str]] = mapped_column(Text)
    teacher_name: Mapped[Optional[str]] = mapped_column(Text)
    nickname_in_class: Mapped[Optional[str]] = mapped_column(Text)

    time_start_year: Mapped[Optional[int]] = mapped_column(SmallInteger)
    time_end_year: Mapped[Optional[int]] = mapped_column(SmallInteger)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="friends")

    user: Mapped[User] = relationship("User", back_populates="school_histories")
    institution: Mapped[Optional[Institution]] = relationship("Institution", back_populates="school_histories")


class UserSchoolAnchor(Base, TimestampMixin):
    __tablename__ = "user_school_anchors"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    institution_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("institutions.id"), index=True
    )

    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    time_start_year: Mapped[Optional[int]] = mapped_column(SmallInteger)
    time_end_year: Mapped[Optional[int]] = mapped_column(SmallInteger)

    region_city: Mapped[Optional[str]] = mapped_column(Text)
    region_district: Mapped[Optional[str]] = mapped_column(Text)

    anchor_embedding: Mapped[Optional[list[float]]] = mapped_column(
        ARRAY(Numeric), nullable=True
    )
    embedding_model: Mapped[Optional[str]] = mapped_column(Text)
    embedded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    match_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped[User] = relationship("User", back_populates="school_anchors")
    institution: Mapped[Optional[Institution]] = relationship("Institution", back_populates="school_anchors")


class UserKeyword(Base):
    __tablename__ = "user_keywords"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    keyword: Mapped[str] = mapped_column(Text, nullable=False)
    weight: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=1.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped[User] = relationship("User", back_populates="keywords")


class UserBlock(Base):
    __tablename__ = "user_blocks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    blocked_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    reason: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


# =========================
# 2. 커뮤니티 도메인
# =========================

class Community(Base, TimestampMixin):
    __tablename__ = "communities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    owner_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    visibility: Mapped[str] = mapped_column(String(20), nullable=False, default="public")
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    posts: Mapped[List["CommunityPost"]] = relationship(
        "CommunityPost", back_populates="community"
    )


class CommunityMember(Base):
    __tablename__ = "community_members"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    community_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("communities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    role: Mapped[str] = mapped_column(String(20), nullable=False, default="member")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    left_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class CommunityPost(Base, TimestampMixin):
    __tablename__ = "community_posts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    community_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("communities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title: Mapped[Optional[str]] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    community: Mapped[Community] = relationship("Community", back_populates="posts")


class CommunityPostImage(Base):
    __tablename__ = "community_post_images"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    post_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("community_posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class CommunityComment(Base, TimestampMixin):
    __tablename__ = "community_comments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    post_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("community_posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    parent_comment_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("community_comments.id", ondelete="CASCADE")
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class CommunityPostLike(Base):
    __tablename__ = "community_post_likes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    post_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("community_posts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


# =========================
# 3. 신고/동기화 – 필요 시 확장 (핵심 매칭/커뮤니티에는 영향 X)
# =========================
# 필요하면 reports, sync_jobs 등도 여기에 추가
