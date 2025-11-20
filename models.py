# path: models.py
"""
Humane / Intersection 전체 DB 모델

- User / UserDetail / Post
- Institution (학교)
- Memory (추억)
- MemoryPersonHint (담임/친구/별명 등 사람 힌트)
- MemoryTag / MemoryTagLink (추억 키워드 태그)
- MatchSession / MatchCandidate (매칭 세션 & 후보)
- BridgeDM (브릿지 DM)
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # 계정 정보
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # 기본 프로필
    name = Column(String(100), nullable=False)
    birth_year = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=True)

    # 학교/지역 정보 (기본 anchor)
    region = Column(String(100), index=True, nullable=False)
    school_name = Column(String(255), index=True, nullable=False)
    school_type = Column(String(20), nullable=False)  # 초/중/고
    admission_year = Column(Integer, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)

    # 감사용
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 관계
    posts = relationship(
        "Post",
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    detail = relationship(
        "UserDetail",
        back_populates="owner",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    memories = relationship(
        "Memory",
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    outgoing_match_sessions = relationship(
        "MatchSession",
        back_populates="requester",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="MatchSession.requester_user_id",
    )
    outgoing_bridge_dms = relationship(
        "BridgeDM",
        back_populates="requester",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="BridgeDM.requester_user_id",
    )
    incoming_bridge_dms = relationship(
        "BridgeDM",
        back_populates="target",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="BridgeDM.target_user_id",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"


class UserDetail(Base):
    __tablename__ = "user_details"

    id = Column(Integer, primary_key=True, index=True)

    transfer_history = Column(String, nullable=True)
    class_info = Column(String(50), nullable=True)
    club_name = Column(String(100), nullable=True)
    nickname = Column(String(100), nullable=True)
    memory_keywords = Column(String, nullable=True)

    # 추가 프로필
    bio = Column(Text, nullable=True)
    profile_image_url = Column(String(500), nullable=True)

    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    owner = relationship("User", back_populates="detail")

    def __repr__(self) -> str:
        return f"<UserDetail id={self.id} owner_id={self.owner_id}>"


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, index=True)
    external_code = Column(String(100), unique=True, nullable=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    type = Column(String(20), nullable=True)  # elem/mid/high/other
    region_city = Column(String(100), nullable=True, index=True)
    region_district = Column(String(100), nullable=True, index=True)
    address = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    memories = relationship("Memory", back_populates="institution")

    def __repr__(self) -> str:
        return f"<Institution id={self.id} name={self.name!r}>"


class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)

    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    owner = relationship("User", back_populates="memories")

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # 시간/지역/학교 anchor
    time_start_year = Column(Integer, nullable=True, index=True)
    time_end_year = Column(Integer, nullable=True)
    region_city = Column(String(100), nullable=True, index=True)
    region_district = Column(String(100), nullable=True, index=True)

    institution_id = Column(
        Integer,
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    institution = relationship("Institution", back_populates="memories")
    custom_school_name = Column(String(255), nullable=True)

    is_public = Column(Boolean, default=True, nullable=False)
    status = Column(String(20), default="active", nullable=False)  # active/hidden/deleted

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    people_hints = relationship(
        "MemoryPersonHint",
        back_populates="memory",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    tag_links = relationship(
        "MemoryTagLink",
        back_populates="memory",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Memory id={self.id} owner_id={self.owner_id}>"


class MemoryPersonHint(Base):
    __tablename__ = "memory_person_hints"

    id = Column(Integer, primary_key=True, index=True)

    memory_id = Column(
        Integer,
        ForeignKey("memories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    memory = relationship("Memory", back_populates="people_hints")

    person_name = Column(String(100), nullable=True)
    person_type = Column(String(20), nullable=True)  # friend/teacher/crush/other
    nickname = Column(String(100), nullable=True)
    description = Column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<MemoryPersonHint id={self.id} memory_id={self.memory_id}>"


class MemoryTag(Base):
    __tablename__ = "memory_tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=True)  # event/place/emotion/etc.

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    links = relationship("MemoryTagLink", back_populates="tag")

    def __repr__(self) -> str:
        return f"<MemoryTag id={self.id} name={self.name!r}>"


class MemoryTagLink(Base):
    __tablename__ = "memory_tag_links"

    id = Column(Integer, primary_key=True, index=True)

    memory_id = Column(
        Integer,
        ForeignKey("memories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tag_id = Column(
        Integer,
        ForeignKey("memory_tags.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    memory = relationship("Memory", back_populates="tag_links")
    tag = relationship("MemoryTag", back_populates="links")

    def __repr__(self) -> str:
        return f"<MemoryTagLink memory_id={self.memory_id} tag_id={self.tag_id}>"


class MatchSession(Base):
    __tablename__ = "match_sessions"

    id = Column(Integer, primary_key=True, index=True)

    requester_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requester = relationship(
        "User",
        back_populates="outgoing_match_sessions",
        foreign_keys=[requester_user_id],
    )

    # 사용자가 입력한 자연어 쿼리 등
    query_text = Column(Text, nullable=True)
    status = Column(
        String(20),
        default="pending",
        nullable=False,
    )  # pending/completed/failed

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    candidates = relationship(
        "MatchCandidate",
        back_populates="session",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<MatchSession id={self.id} requester_user_id={self.requester_user_id}>"


class MatchCandidate(Base):
    __tablename__ = "match_candidates"

    id = Column(Integer, primary_key=True, index=True)

    session_id = Column(
        Integer,
        ForeignKey("match_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session = relationship("MatchSession", back_populates="candidates")

    candidate_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_user = relationship("User")

    matched_memory_id = Column(
        Integer,
        ForeignKey("memories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    matched_memory = relationship("Memory")

    score = Column(Float, nullable=True)
    rank = Column(Integer, nullable=True)

    status = Column(
        String(20),
        default="suggested",
        nullable=False,
    )  # suggested/liked/skipped/connected

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<MatchCandidate id={self.id} session_id={self.session_id} "
            f"candidate_user_id={self.candidate_user_id}>"
        )


class BridgeDM(Base):
    __tablename__ = "bridge_dms"

    id = Column(Integer, primary_key=True, index=True)

    requester_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requester = relationship(
        "User",
        back_populates="outgoing_bridge_dms",
        foreign_keys=[requester_user_id],
    )

    target_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target = relationship(
        "User",
        back_populates="incoming_bridge_dms",
        foreign_keys=[target_user_id],
    )

    match_session_id = Column(
        Integer,
        ForeignKey("match_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    match_session = relationship("MatchSession")

    initial_message = Column(Text, nullable=True)

    status = Column(
        String(20),
        default="pending",
        nullable=False,
    )  # pending/accepted/rejected/blocked

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    responded_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<BridgeDM id={self.id} requester_user_id={self.requester_user_id} "
            f"target_user_id={self.target_user_id}>"
        )


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True, nullable=False)
    content = Column(Text, nullable=False)

    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    owner = relationship("User", back_populates="posts")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Post id={self.id} owner_id={self.owner_id}>"
