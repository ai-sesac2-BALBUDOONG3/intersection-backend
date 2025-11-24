from sqlalchemy.orm import Session
import models
import schemas
import security


# ----------------------------------------------------
# 1. 회원 조회
# ----------------------------------------------------
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


# ----------------------------------------------------
# 2. 회원 생성 (회원가입)
# ----------------------------------------------------
def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.get_password_hash(user.password)

    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        name=user.name,
        birth_year=user.birth_year,
        gender=user.gender,
        region=user.region,
        school_name=user.school_name,
        school_type=user.school_type,
        admission_year=user.admission_year
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# ----------------------------------------------------
# 3. 추가 정보 생성/수정
# ----------------------------------------------------
def create_user_detail(db: Session, detail: schemas.UserDetailCreate, user_id: int):
    db_detail = (
        db.query(models.UserDetail)
        .filter(models.UserDetail.owner_id == user_id)
        .first()
    )

    if db_detail:
        db_detail.transfer_history = detail.transfer_history
        db_detail.class_info = detail.class_info
        db_detail.club_name = detail.club_name
        db_detail.nickname = detail.nickname
        db_detail.memory_keywords = detail.memory_keywords
    else:
        db_detail = models.UserDetail(**detail.dict(), owner_id=user_id)
        db.add(db_detail)

    db.commit()
    db.refresh(db_detail)
    return db_detail


# ----------------------------------------------------
# 4. 게시물 조회
# ----------------------------------------------------
def get_posts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Post).offset(skip).limit(limit).all()


# ----------------------------------------------------
# 5. 게시물 생성
# ----------------------------------------------------
def create_user_post(db: Session, post: schemas.PostCreate, user_id: int):
    db_post = models.Post(**post.dict(), owner_id=user_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


# ----------------------------------------------------
# 6. 추천 친구 로직
# ----------------------------------------------------
def get_recommended_users(db: Session, current_user: models.User, limit: int = 20):

    all_users = (
        db.query(models.User)
        .filter(models.User.id != current_user.id)
        .all()
    )

    scored = []

    for u in all_users:
        score = 0

        if u.school_name == current_user.school_name:
            score += 50

        if u.region == current_user.region:
            score += 30

        if abs(u.admission_year - current_user.admission_year) <= 1:
            score += 15

        if abs(u.birth_year - current_user.birth_year) <= 1:
            score += 10

        scored.append((u, score))

    scored.sort(key=lambda x: x[1], reverse=True)

    return [user for user, score in scored[:limit]]


# ----------------------------------------------------
# 7. 친구 추가
# ----------------------------------------------------
def add_friend(db: Session, user_id: int, target_user_id: int):
    friendship = models.Friend(
        user_id=user_id,
        friend_id=target_user_id
    )
    db.add(friendship)
    db.commit()
    db.refresh(friendship)
    return friendship


# ----------------------------------------------------
# 8. 친구목록 조회
# ----------------------------------------------------
def get_my_friends(db: Session, user_id: int):
    """현재 유저의 친구 목록(User 객체) 반환"""

    friendships = (
        db.query(models.Friend)
        .filter(models.Friend.user_id == user_id)
        .all()
    )

    friend_ids = [f.friend_id for f in friendships]

    if not friend_ids:
        return []

    return (
        db.query(models.User)
        .filter(models.User.id.in_(friend_ids))
        .all()
    )
