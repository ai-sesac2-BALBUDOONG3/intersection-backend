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
    name = Column(String, nullable=False)       # 실명 (PASS 인증 전제)
    birth_year = Column(Integer, nullable=False) # 출생연도 (수정 불가 로직용)
    gender = Column(String, nullable=True)       # 성별
    
    # [Step 3: 학교/지역 정보 (교집합 매칭용)]
    region = Column(String, index=True, nullable=False)      # 거주 지역
    school_name = Column(String, index=True, nullable=False) # 학교명
    school_type = Column(String, nullable=False)             # 초/중/고 구분
    admission_year = Column(Integer, nullable=False)         # 입학년도

    is_active = Column(Boolean, default=True)

    # 관계 설정
    posts = relationship("Post", back_populates="owner")
    # [⚡️ 추가] 추가 정보와 1:1 연결
    detail = relationship("UserDetail", back_populates="owner", uselist=False)


# [ ⚡️ (신규!) 추가 정보 (Step 4) ]
class UserDetail(Base):
    __tablename__ = "user_details"

    id = Column(Integer, primary_key=True, index=True)
    
    # 세부 학교 이력
    transfer_history = Column(String, nullable=True) # 전학 이력
    class_info = Column(String, nullable=True)       # 반 정보 (예: 3학년 2반)
    club_name = Column(String, nullable=True)        # 동아리
    nickname = Column(String, nullable=True)         # 당시 별명
    
    # 추억 키워드 (쉼표로 구분해서 저장, 예: "매점,체육대회,떡볶이")
    memory_keywords = Column(String, nullable=True)
    
    # 주인님(User)과 연결
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