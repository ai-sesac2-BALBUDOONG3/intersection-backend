# app/models/user_school_history.py

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


class UserSchoolHistory(Base):
    __tablename__ = "user_school_histories"

    id = Column(BigInteger, primary_key=True, index=True)

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # 학교 마스터(institutions.id)와 연결 (선택)
    institution_id = Column(
        BigInteger,
        ForeignKey("institutions.id"),
        nullable=True,
    )

    # 사용자가 기억하는 학교명 (직접 입력 + 마스터 혼합 가능)
    school_name = Column(String, nullable=False)

    region_city = Column(String, nullable=True)
    region_district = Column(String, nullable=True)

    # 재학/근무 시기 (연단위)
    time_start_year = Column(Integer, nullable=True)
    time_end_year = Column(Integer, nullable=True)

    # 학년/반/담임 등
    grade = Column(String, nullable=True)
    class_name = Column(String, nullable=True)
    homeroom_teacher_name = Column(String, nullable=True)

    memo = Column(Text, nullable=True)

    is_deleted = Column(
        Boolean,
        nullable=False,
        server_default="false",
    )

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
