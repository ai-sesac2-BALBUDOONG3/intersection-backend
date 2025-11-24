from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

# [ 1. 기본 회원 정보 (Step 1~3) ]
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    # [Step 1: 계정 정보]
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # [Step 2: 기본 프로필]
    name = Column(String, nullable=False)          # 실명
    birth_year = Column(Integer, nullable=False)   # 출생연도
    gender = Column(String, nullable=True)         # 성별 (선택)
    
    # [Step 3: 학교/지역 정보]
    region = Column(String, index=True, nullable=False)       # 지역
    school_name = Column(String, index=True, nullable=False)  # 학교명
    school_type = Column(String, nullable=False)              # 초/중/고
    admission_year = Column(Integer, nullable=False)          # 입학년도

    # ⚡️ 핵심 수정 포인트: null 불가 + default True
    is_active = Column(Boolean, default=True, nullable=False)

    # 관계 설정
    posts = relationship("Post", back_populates="owner")
    detail = relationship("UserDetail", back_populates="owner", uselist=False)


# [ 2. 추가 정보 (Step 4) ]
class UserDetail(Base):
    __tablename__ = "user_details"

    id = Column(Integer, primary_key=True, index=True)
    
    transfer_history = Column(String, nullable=True)  # 전학 이력
    class_info = Column(String, nullable=True)        # 반 정보
    club_name = Column(String, nullable=True)         # 동아리
    nickname = Column(String, nullable=True)          # 별명
    memory_keywords = Column(String, nullable=True)   # 추억 키워드

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="detail")


# [ 3. 게시물 ]
class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="posts")
#친구목록
class Friend(Base):
    __tablename__ = "friends"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    friend_id = Column(Integer, ForeignKey("users.id"), nullable=False)
