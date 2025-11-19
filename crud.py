from sqlalchemy.orm import Session
import models
import schemas
import security

# --- 1. 회원 '조회' 기능 ---
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

# --- 2. 회원 '등록' 기능 (콤마 수정 완료!) ---
def create_user(db: Session, user: schemas.UserCreate):
    
    # 비밀번호 암호화
    hashed_password = security.get_password_hash(user.password)
    
    # 명세서에 맞춘 '새 회원' 정보 준비
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        name=user.name,
        birth_year=user.birth_year,
        gender=user.gender,
        region=user.region,
        school_name=user.school_name,
        school_type=user.school_type,
        admission_year=user.admission_year  # <--- 여기 콤마들은 잘 챙겨야 합니다!
    )
    
    # 저장
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- 3. 게시물 목록 조회 ---
def get_posts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Post).offset(skip).limit(limit).all()

# --- 4. 게시물 생성 ---
def create_user_post(db: Session, post: schemas.PostCreate, user_id: int):
    db_post = models.Post(**post.dict(), owner_id=user_id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post