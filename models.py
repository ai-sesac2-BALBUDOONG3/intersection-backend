# path: models.py
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from database import Base


# ============================================================
# 1. 사용자 / 인증 / 프로필 / 차단 / 친구
# ============================================================


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # 로그인 계정
    login_id = Column(Text, nullable=False, unique=True, index=True)  # intersection ID
    password_hash = Column(Text, nullable=False)

    # 기본 프로필
    real_name = Column(Text, nullable=False)
    nickname = Column(Text, nullable=False)
    email = Column(Text, unique=True)
    phone = Column(Text, unique=True)
    birth_year = Column(SmallInteger, nullable=False)
    gender = Column(String(10))  # 'male','female','other'

    # 실명인증
    is_verified = Column(Boolean, nullable=False, server_default="false")
    verification_provider = Column(String(50))
    verification_at = Column(DateTime(timezone=True))

    # 계정 상태
    status = Column(String(20), nullable=False, server_default="active")
    signup_step = Column(SmallInteger, nullable=False, server_default="4")

    # 공통 메타
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    is_deleted = Column(Boolean, nullable=False, server_default="false")
    deleted_at = Column(DateTime(timezone=True))

    # 관계
    profile = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    school_anchors = relationship(
        "UserSchoolAnchor",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    school_histories = relationship(
        "UserSchoolHistory",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    keywords = relationship(
        "UserKeyword",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    residence_city = Column(Text)         # 시/도
    residence_district = Column(Text)     # 구/군
    residence_neighborhood = Column(Text) # 동/읍/면

    profile_visibility = Column(
        String(20), nullable=False, server_default="friends"
    )  # 'public','friends','private'

    # AI 추천용(지금은 타입만 맞춰두고 실제 임베딩 로직은 나중에)
    matching_embedding = Column(
        Text, nullable=True
    )  # vector(1536)를 쓰려면 pgvector 확장 필요. 지금은 Text로 placeholder.
    embedding_model = Column(String(100))
    embedding_model_version = Column(String(50))
    embedding_dimension = Column(SmallInteger)
    embedded_at = Column(DateTime(timezone=True))

    updated_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user = relationship("User", back_populates="profile")


class UserBlock(Base):
    __tablename__ = "user_blocks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    blocker_user_id = Column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    blocked_user_id = Column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    reason = Column(Text)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class UserFriendship(Base):
    __tablename__ = "user_friendships"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    friend_user_id = Column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status = Column(String(20), nullable=False, server_default="pending")
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


# ============================================================
# 2. 기관(학교) / 동기화
# ============================================================


class SyncJob(Base):
    __tablename__ = "sync_jobs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    external_source = Column(String(50), nullable=False)
    started_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finished_at = Column(DateTime(timezone=True))
    status = Column(String(20), nullable=False, server_default="running")
    fetched_count = Column(Integer, nullable=False, server_default="0")
    upserted_count = Column(Integer, nullable=False, server_default="0")
    deleted_count = Column(Integer, nullable=False, server_default="0")
    error_message = Column(Text)


class InstitutionRaw(Base):
    __tablename__ = "institution_raw"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sync_job_id = Column(
        BigInteger, ForeignKey("sync_jobs.id", ondelete="CASCADE"), nullable=False
    )
    external_source = Column(String(50), nullable=False)
    external_id = Column(Text, nullable=False)
    payload = Column(Text, nullable=False)  # JSONB → Text 로 placeholder
    received_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    processed = Column(Boolean, nullable=False, server_default="false")
    processed_at = Column(DateTime(timezone=True))


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    external_source = Column(String(50), nullable=False)
    external_id = Column(Text, nullable=False)

    name = Column(Text, nullable=False)
    name_normalized = Column(Text)

    institution_type = Column(String(30), nullable=False)

    country_code = Column(String(2), nullable=False, server_default="KR")

    region_city = Column(Text)
    region_district = Column(Text)
    region_neighborhood = Column(Text)

    address = Column(Text)
    postal_code = Column(Text)

    latitude = Column(Numeric(9, 6))
    longitude = Column(Numeric(9, 6))

    is_active = Column(Boolean, nullable=False, server_default="true")

    opened_at = Column(Date)
    closed_at = Column(Date)

    last_synced_at = Column(DateTime(timezone=True))
    last_sync_job_id = Column(BigInteger)


# ============================================================
# 3. 사용자 학교 정보 / 키워드
# ============================================================


class UserSchoolAnchor(Base):
    __tablename__ = "user_school_anchors"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    institution_id = Column(
        BigInteger, ForeignKey("institutions.id"), nullable=False
    )
    school_level = Column(String(20), nullable=False)  # 'elementary','middle','high'
    entry_year = Column(SmallInteger, nullable=False)
    graduation_year = Column(SmallInteger)
    is_primary = Column(Boolean, nullable=False, server_default="true")

    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user = relationship("User", back_populates="school_anchors")
    institution = relationship("Institution")


class UserSchoolHistory(Base):
    __tablename__ = "user_school_histories"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    institution_id = Column(
        BigInteger, ForeignKey("institutions.id"), nullable=False
    )

    school_level = Column(String(20), nullable=False)
    start_year = Column(SmallInteger)
    end_year = Column(SmallInteger)
    grade = Column(SmallInteger)
    class_group = Column(Text)
    homeroom_teacher = Column(Text)
    club_name = Column(Text)
    nickname_in_class = Column(Text)
    is_transfer = Column(Boolean, nullable=False, server_default="false")
    notes = Column(Text)

    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user = relationship("User", back_populates="school_histories")
    institution = relationship("Institution")


class UserKeyword(Base):
    __tablename__ = "user_keywords"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    keyword = Column(Text, nullable=False)
    weight = Column(SmallInteger)

    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    user = relationship("User", back_populates="keywords")


# ============================================================
# 4. 커뮤니티 / 게시글 / 댓글 / 신고 (간단 버전)
# ============================================================


class Community(Base):
    __tablename__ = "communities"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    institution_id = Column(
        BigInteger, ForeignKey("institutions.id"), nullable=False
    )
    school_level = Column(String(20), nullable=False)
    entry_year = Column(SmallInteger, nullable=False)
    residence_city = Column(Text)
    residence_district = Column(Text)

    name = Column(Text, nullable=False)
    description = Column(Text)
    status = Column(String(20), nullable=False, server_default="active")

    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class CommunityMember(Base):
    __tablename__ = "community_members"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    community_id = Column(
        BigInteger, ForeignKey("communities.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role = Column(String(20), nullable=False, server_default="member")
    joined_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    last_seen_at = Column(DateTime(timezone=True))


class CommunityPost(Base):
    __tablename__ = "community_posts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    community_id = Column(
        BigInteger, ForeignKey("communities.id", ondelete="CASCADE"), nullable=False
    )
    author_user_id = Column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    content = Column(Text, nullable=False)
    image_count = Column(SmallInteger, nullable=False, server_default="0")

    like_count = Column(Integer, nullable=False, server_default="0")
    comment_count = Column(Integer, nullable=False, server_default="0")

    status = Column(String(20), nullable=False, server_default="active")
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    is_deleted = Column(Boolean, nullable=False, server_default="false")
    deleted_at = Column(DateTime(timezone=True))


class CommunityComment(Base):
    __tablename__ = "community_comments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    post_id = Column(
        BigInteger,
        ForeignKey("community_posts.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    parent_comment_id = Column(
        BigInteger, ForeignKey("community_comments.id"), nullable=True
    )

    content = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, server_default="active")

    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    is_deleted = Column(Boolean, nullable=False, server_default="false")
    deleted_at = Column(DateTime(timezone=True))


class Report(Base):
    __tablename__ = "reports"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    reporter_user_id = Column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    reported_user_id = Column(BigInteger, ForeignKey("users.id"))
    target_type = Column(String(30), nullable=False)
    target_id = Column(BigInteger, nullable=False)
    reason_category = Column(String(50))
    reason_text = Column(Text)
    status = Column(String(20), nullable=False, server_default="pending")
    resolved_by_user_id = Column(BigInteger, ForeignKey("users.id"))
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    resolved_at = Column(DateTime(timezone=True))
