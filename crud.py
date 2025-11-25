from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from typing import Optional # 👈 타입 힌트를 위해 추가
import models
import schemas
from security import get_password_hash # 비밀번호 해싱 함수를 사용하기 위해 필요

# --- [ User (사용자) 관련 CRUD 함수 ] ---

def get_user_by_email(db: Session, email: str):
    """이메일로 사용자를 조회합니다. (일반 로그인용)"""
    return db.query(models.User).filter(models.User.email == email).first()

# ⭐️ 추가: 카카오 ID로 사용자를 조회합니다. (소셜 로그인용)
def get_user_by_kakao_id(db: Session, kakao_id: str):
    """카카오 ID로 사용자를 조회합니다."""
    return db.query(models.User).filter(models.User.kakao_id == kakao_id).first()


def create_user(db: Session, user: schemas.UserCreate):
    """새로운 일반 사용자를 생성합니다 (회원가입)."""
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        name=user.name,
        birth_year=user.birth_year,
        gender=user.gender,
        region=user.region,
        school_name=user.school_name,
        school_type=user.school_type,
        admission_year=user.admission_year,
        kakao_id=None # 일반 회원은 카카오 ID가 없습니다.
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# ⭐️ 추가: 소셜 로그인으로 사용자 생성 (최초 로그인 시)
def create_social_user(db: Session, kakao_id: str, nickname: str, email: Optional[str] = None):
    """
    카카오 최초 로그인 시, 새로운 사용자를 생성합니다.
    필수 필드는 임시 값으로 채워 넣습니다.
    """
    temp_hashed_password = get_password_hash("SOCIAL_LOGIN_USER") 
    temp_email = email if email else f"kakao_{kakao_id}@social.com"
    
    db_user = models.User(
        email=temp_email, 
        hashed_password=temp_hashed_password,
        name=nickname, 
        kakao_id=kakao_id, # ⭐️ 고유 카카오 ID 저장
        
        # 필수 필드 임시 값
        birth_year=2000, 
        region="미입력",
        school_name="미입력",
        school_type="미입력",
        admission_year=2020,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# --- [ UserDetail (추가 정보) 관련 CRUD 함수 ] ---

def create_user_detail(db: Session, detail: schemas.UserDetailCreate, user_id: int):
    """사용자의 추가 정보를 생성합니다."""
    db_detail = models.UserDetail(
        **detail.model_dump(),
        owner_id=user_id
    )
    db.add(db_detail)
    try:
        db.commit()
        db.refresh(db_detail)
        return db_detail
    except IntegrityError:
        db.rollback()
        raise ValueError("이미 사용자 상세 정보가 등록되어 있습니다.")

# --- [ Post (게시글) 관련 CRUD 함수 ] ---

def create_user_post(db: Session, post: schemas.PostCreate, user_id: int):
    """사용자 ID에 연결된 새 게시글을 생성합니다."""
    db_post = models.Post(
        title=post.title, 
        content=post.content, 
        owner_id=user_id
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

def get_posts(db: Session, skip: int = 0, limit: int = 100):
    """모든 게시글을 최신순으로 조회합니다."""
    return db.query(models.Post).order_by(models.Post.updated_at.desc()).offset(skip).limit(limit).all()

def update_post(db: Session, post_id: int, post_update: schemas.PostUpdate, user_id: int):
    """게시글을 수정합니다. (작성자 확인 필수)"""
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    
    if db_post is None:
        return None  # 게시글이 없음 (404)

    if db_post.owner_id != user_id:
        return "not_owner" # 작성자가 아님 (403)
    
    db_post.title = post_update.title
    db_post.content = post_update.content
    
    db.commit()
    db.refresh(db_post)
    return db_post

def delete_post(db: Session, post_id: int, user_id: int):
    """게시글을 삭제합니다. (작성자 확인 필수)"""
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    
    if db_post is None:
        return None # 게시글이 없음 (404)

    if db_post.owner_id != user_id:
        return "not_owner" # 작성자가 아님 (403)
    
    # 해당 게시글의 모든 댓글도 함께 삭제
    db.query(models.Comment).filter(models.Comment.post_id == post_id).delete(synchronize_session=False)
    
    db.delete(db_post)
    db.commit()
    return True

# --- [ Friend (친구) 관련 CRUD 함수 ] ---

def get_recommended_users(db: Session, current_user: models.User):
    """현재 사용자의 학교/지역이 같은 추천 친구 목록을 조회합니다."""
    
    friend_ids_as_user = db.query(models.Friend.friend_id).filter(models.Friend.user_id == current_user.id)
    friend_ids_as_friend = db.query(models.Friend.user_id).filter(models.Friend.friend_id == current_user.id)
    
    exclude_ids = [current_user.id] + [f[0] for f in friend_ids_as_user] + [f[0] for f in friend_ids_as_friend]
    
    recommendations = db.query(models.User).filter(
        or_(
            models.User.school_name == current_user.school_name,
            models.User.region == current_user.region
        ),
        models.User.id.notin_(exclude_ids)
    ).limit(50).all() 
    
    return recommendations

def add_friend(db: Session, user_id: int, target_user_id: int):
    """친구 관계를 추가합니다. (단방향 요청으로 가정)"""
    if user_id == target_user_id:
        raise ValueError("자기 자신을 친구로 추가할 수 없습니다.")

    existing_friendship = db.query(models.Friend).filter(
        or_(
            (models.Friend.user_id == user_id) & (models.Friend.friend_id == target_user_id),
            (models.Friend.user_id == target_user_id) & (models.Friend.friend_id == user_id)
        )
    ).first()

    if existing_friendship:
        raise ValueError("이미 친구 관계이거나 요청 대기 중입니다.")
    
    db_friend = models.Friend(
        user_id=user_id, 
        friend_id=target_user_id
    )
    db.add(db_friend)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("데이터베이스 오류로 친구 추가에 실패했습니다.")


def get_my_friends(db: Session, user_id: int):
    """내가 친구로 등록한 사용자 목록을 조회합니다."""
    
    sent_friends = db.query(models.Friend.friend_id).filter(models.Friend.user_id == user_id).all()
    received_friends = db.query(models.Friend.user_id).filter(models.Friend.friend_id == user_id).all()
    
    all_friend_ids = set([f[0] for f in sent_friends] + [f[0] for f in received_friends])
    
    if not all_friend_ids:
        return []

    friends = db.query(models.User).filter(models.User.id.in_(all_friend_ids)).all()
    return friends

# --- [ Comment (댓글) 관련 CRUD 함수 ] ---

def create_comment(db: Session, comment: schemas.CommentCreate, user_id: int, post_id: int):
    """특정 게시글에 댓글을 작성합니다."""
    db_comment = models.Comment(
        content=comment.content, 
        owner_id=user_id, 
        post_id=post_id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

def get_comments_by_post(db: Session, post_id: int):
    """특정 게시글의 댓글 목록을 작성 시간순으로 조회합니다."""
    comments = db.query(models.Comment).filter(
        models.Comment.post_id == post_id
    ).order_by(models.Comment.created_at.asc()).all()
    
    return comments