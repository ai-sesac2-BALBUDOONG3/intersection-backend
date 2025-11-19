from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base 

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    # [ 1. 계정 정보 ]
    email = Column(String, unique=True, index=True, nullable=False) # 아이디(이메일)
    hashed_password = Column(String, nullable=False) # 비밀번호
    
    # [ 2. 기본 프로필 ] - 명세서 반영!
    name = Column(String, nullable=False) # 실명 (필수)
    birth_year = Column(Integer, nullable=False) # 출생연도 (필수)
    gender = Column(String, nullable=True) # 성별 (선택)
    
    # [ 3. 학교/지역 정보 ] - 명세서 반영!
    region = Column(String, index=True, nullable=False) # 거주 지역 (필수)
    school_name = Column(String, index=True, nullable=False) # 학교명 (필수)
    school_type = Column(String, nullable=False) # 초/중/고 구분 (필수)
    admission_year = Column(Integer, nullable=False) # 입학년도 (필수)

    # [ 4. 시스템 관리용 ]
    is_active = Column(Boolean, default=True)

    # 관계 설정 (게시물)
    posts = relationship("Post", back_populates="owner")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="posts")