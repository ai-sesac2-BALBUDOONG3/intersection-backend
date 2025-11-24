from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

# [ 1. 기본 회원 정보 ]
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    # [계정 정보]
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
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


# [ 2. 추가 정보 ]
class UserDetail(Base):
    __tablename__ = "user_details"

    id = Column(Integer, primary_key=True, index=True)
    
    transfer_history = Column(String, nullable=True)
    class_info = Column(String, nullable=True)
    club_name = Column(String, nullable=True)
    nickname = Column(String, nullable=True)
    memory_keywords = Column(String, nullable=True)

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
    comments = relationship("Comment", back_populates="post")


# [ 4. 친구 목록 ]
class Friend(Base):
    __tablename__ = "friends"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    friend_id = Column(Integer, ForeignKey("users.id"), nullable=False)


# [ 5. 댓글 ]
class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    
    owner_id = Column(Integer, ForeignKey("users.id"))
    post_id = Column(Integer, ForeignKey("posts.id"))

    owner = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")