# app/models/community.py

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.db.session import Base


class Community(Base):
    __tablename__ = "communities"

    id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    created_by_user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    is_private = Column(Boolean, nullable=False, server_default="false")

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class CommunityPost(Base):
    __tablename__ = "community_posts"

    id = Column(BigInteger, primary_key=True, index=True)
    community_id = Column(
        BigInteger,
        ForeignKey("communities.id"),
        nullable=False,
        index=True,
    )
    author_user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)

    is_deleted = Column(Boolean, nullable=False, server_default="false")

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class CommunityComment(Base):
    __tablename__ = "community_comments"

    id = Column(BigInteger, primary_key=True, index=True)
    post_id = Column(
        BigInteger,
        ForeignKey("community_posts.id"),
        nullable=False,
        index=True,
    )
    author_user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    parent_comment_id = Column(
        BigInteger,
        ForeignKey("community_comments.id"),
        nullable=True,
    )

    content = Column(Text, nullable=False)

    is_deleted = Column(Boolean, nullable=False, server_default="false")

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
