from sqlalchemy.orm import Session
from passlib.context import CryptContext
import models, schemas

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# 1. 유저 조회
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

# 2. 유저 생성
def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
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
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# 3. 상세 정보 생성
def create_user_detail(db: Session, detail: schemas.UserDetailCreate, user_id: int):
    db_detail = models.UserDetail(**detail.dict(), owner_id=user_id)
    db.add(db_detail)
    db.commit()
    db.refresh(db_detail)
    return db_detail

# 4. 게시글 생성
def create_user_post(db: Session, post: schemas.PostCreate, user_id: int):
    db_post = models.Post(**post.dict(), owner_id=user_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

# 5. 게시글 목록 조회
def get_posts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Post).offset(skip).limit(limit).all()

# 6. 친구 추천 (같은 학교/입학년도)
def get_recommended_users(db: Session, current_user: models.User):
    return db.query(models.User).filter(
        models.User.school_name == current_user.school_name,
        models.User.admission_year == current_user.admission_year,
        models.User.id != current_user.id
    ).all()

# 7. 친구 추가
def add_friend(db: Session, user_id: int, friend_id: int):
    db_friend = models.Friend(user_id=user_id, friend_id=friend_id)
    db.add(db_friend)
    db.commit()
    return db_friend

# 8. 내 친구 목록
def get_my_friends(db: Session, user_id: int):
    friend_links = db.query(models.Friend).filter(models.Friend.user_id == user_id).all()
    friend_ids = [f.friend_id for f in friend_links]
    return db.query(models.User).filter(models.User.id.in_(friend_ids)).all()

# --- [새로 추가된 부분] ---

# 9. 게시글 수정
def update_post(db: Session, post_id: int, post_update: schemas.PostUpdate, user_id: int):
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        return None
    if db_post.owner_id != user_id:
        return "not_owner"
    
    db_post.title = post_update.title
    db_post.content = post_update.content
    db.commit()
    db.refresh(db_post)
    return db_post

# 10. 게시글 삭제
def delete_post(db: Session, post_id: int, user_id: int):
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not db_post:
        return None
    if db_post.owner_id != user_id:
        return "not_owner"

    db.delete(db_post)
    db.commit()
    return True

# 11. 댓글 작성
def create_comment(db: Session, comment: schemas.CommentCreate, user_id: int, post_id: int):
    db_comment = models.Comment(**comment.dict(), owner_id=user_id, post_id=post_id)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

# 12. 댓글 조회
def get_comments_by_post(db: Session, post_id: int):
    return db.query(models.Comment).filter(models.Comment.post_id == post_id).all()