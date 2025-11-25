from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func # 👈 시간 자동 기록을 위한 함수
from database import Base # 기존 database 파일 사용

# [ 1. 기본 회원 정보 ]
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    # [계정 정보]
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # ⭐️ 카카오 로그인 추가 필드 ⭐️
    kakao_id = Column(String, unique=True, index=True, nullable=True) # 👈 카카오 고유 ID (추가됨)
    
    # [기본 프로필]
    name = Column(String, nullable=False)
    birth_year = Column(Integer, nullable=False)
    gender = Column(String, nullable=True)
    
    # [학교/지역 정보]
    region = Column(String, index=True, nullable=False)
    school_name = Column(String, index=True, nullable=False)
    school_type = Column(String, nullable=False)
    admission_year = Column(Integer, nullable=False)

    # [📷 사진 기능 추가!] 프로필 사진 주소 저장하는 칸
    profile_image = Column(String, nullable=True)

    # 계정 활성 상태
    is_active = Column(Boolean, default=True, nullable=False)

    # [⚡️ 관계 설정]
    posts = relationship("Post", back_populates="owner")
    detail = relationship("UserDetail", back_populates="owner", uselist=False)
    comments = relationship("Comment", back_populates="owner")
    
    # 🌟 친구 관계 설정 수정 (Friend 모델에 맞게 양방향 관계 재설정)
    # 내가 친구 요청한 목록
    friends_sent = relationship("Friend", foreign_keys='Friend.user_id', back_populates="user")
    # 나에게 친구 요청한 목록 (내가 '친구'로 등록된 경우)
    friends_received = relationship("Friend", foreign_keys='Friend.friend_id', back_populates="friend")


# [ 2. 추가 정보 ]
class UserDetail(Base):
    __tablename__ = "user_details"
    
    id = Column(Integer, primary_key=True, index=True)
    
    transfer_history = Column(String, nullable=True)
    class_info = Column(String, nullable=True)
    club_name = Column(String, nullable=True)
    nickname = Column(String, nullable=True)
    memory_keywords = Column(String, nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id"), unique=True) # 👈 1:1 관계를 위해 unique=True
    owner = relationship("User", back_populates="detail")


# [ 3. 게시물 ]
class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text) # 👈 Text 타입 권장
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # 🌟 추가 1: 게시글 작성 시간
    created_at = Column(DateTime, default=func.now())
    # 🌟 추가 2: 게시글 수정 시간 (수정될 때마다 자동으로 업데이트)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now()) 

    owner = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post")


# [ 4. 친구 목록 ]
class Friend(Base):
    __tablename__ = "friends"

    __table_args__ = (
        UniqueConstraint('user_id', 'friend_id', name='_user_friend_uc'),
    )

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True, nullable=False)
    friend_id = Column(Integer, ForeignKey("users.id"), primary_key=True, nullable=False)
    
    # 🌟 추가: 친구 관계를 맺은 시간 (언제 친구가 되었는지 기록)
    created_at = Column(DateTime, default=func.now())
    
    # [⚡️ 관계 설정]
    user = relationship("User", foreign_keys=[user_id], back_populates="friends_sent")
    friend = relationship("User", foreign_keys=[friend_id], back_populates="friends_received")


# [ 5. 댓글 ]
class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text) # 👈 Text 타입 권장
    
    owner_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))
    
    # 🌟 추가 3: 댓글 작성 시간 (언제 작성했는지 기록)
    created_at = Column(DateTime, default=func.now())

    owner = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")