# app/models/user.py

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # intersection 로그인용 ID (unique)
    login_id = Column(String, unique=True, nullable=False, index=True)

    # 해시된 비밀번호
    password_hash = Column(Text, nullable=False)

    # 실명 / 닉네임
    real_name = Column(String, nullable=False)
    nickname = Column(String, nullable=False)

    # 이메일 (nullable)
    email = Column(String, nullable=True, unique=False)

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
