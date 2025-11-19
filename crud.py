from sqlalchemy.orm import Session
import models
import schemas
import security

# --- 1. 회원 '조회' 기능 ---
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

# --- 2. 회원 '등록' 기능 (콤마 수정 완료!) ---
# --- [ ⚡️ (수정!) Step 1~3: 기본 회원 가입 ] ---
def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = security.get_password_hash(user.password)
    
    # 여기서는 'User' 테이블에만 저장합니다!
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

# --- [ ⚡️ (신규!) Step 4: 추가 정보 등록 ] ---
def create_user_detail(db: Session, detail: schemas.UserDetailCreate, user_id: int):
    # 혹시 이미 등록된 게 있는지 확인 (수정 대비)
    db_detail = db.query(models.UserDetail).filter(models.UserDetail.owner_id == user_id).first()
    
    if db_detail:
        # 있으면 내용 수정
        db_detail.transfer_history = detail.transfer_history
        db_detail.class_info = detail.class_info
        db_detail.club_name = detail.club_name
        db_detail.nickname = detail.nickname
        db_detail.memory_keywords = detail.memory_keywords
    else:
        # 없으면 새로 등록
        db_detail = models.UserDetail(**detail.dict(), owner_id=user_id)
        db.add(db_detail)
        
    db.commit()
    db.refresh(db_detail)
    return db_detail

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