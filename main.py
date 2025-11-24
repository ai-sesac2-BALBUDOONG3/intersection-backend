from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List
from fastapi.middleware.cors import CORSMiddleware

# 내부 모듈
import models
import schemas
import crud
import security
from database import SessionLocal, engine

# -----------------------------
# DB 테이블 자동 생성
# -----------------------------
models.Base.metadata.create_all(bind=engine)

# -----------------------------
# FastAPI 객체 생성
# -----------------------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 개발 단계에서는 모든 출처 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# -----------------------------
# DB 세션 자동관리
# -----------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------
# 기본 확인용 엔드포인트
# -----------------------------
@app.get("/")
def read_root():
    return {"message": "인터섹션 백엔드 기지에 오신 것을 환영합니다!"}


# -----------------------------
# 1. 회원가입
# -----------------------------
@app.post("/users/", response_model=schemas.User)
def create_user_endpoint(
    user_data: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    db_user = crud.get_user_by_email(db, email=user_data.email)
    if db_user:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")

    new_user = crud.create_user(db=db, user=user_data)
    return new_user


# -----------------------------
# 2. 로그인(JSON) → JWT 발급
# -----------------------------
@app.post("/token", response_model=schemas.Token)
def login_for_access_token(
    login_data: schemas.LoginRequest,    # ⭐ JSON Body Pydantic 모델
    db: Session = Depends(get_db)
):
    email = login_data.email
    password = login_data.password

    # 유저 조회
    user = crud.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=401, detail="존재하지 않는 이메일입니다.")

    # 비밀번호 검증
    if not security.verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="비밀번호가 잘못되었습니다.")

    # JWT 생성
    token_data = {"sub": user.email}
    access_token = security.create_access_token(data=token_data)

    return {"access_token": access_token, "token_type": "bearer"}


# -----------------------------
# 3. 현재 로그인된 사용자 조회
# -----------------------------
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="출입증(Token)이 유효하지 않습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = security.verify_token(token, credentials_exception)
    email: str = payload.get("sub")

    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception

    return user


# -----------------------------
# 4. 추가 정보 입력
# -----------------------------
@app.post("/users/me/details", response_model=schemas.UserDetail)
def create_details_endpoint(
    detail_data: schemas.UserDetailCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    detail = crud.create_user_detail(db=db, detail=detail_data, user_id=current_user.id)
    return detail


# -----------------------------
# 5. 현재 로그인한 사용자 정보
# -----------------------------
@app.get("/users/me", response_model=schemas.User)
def read_users_me(
    current_user: schemas.User = Depends(get_current_user)
):
    return current_user


# -----------------------------
# 6. 게시물 생성
# -----------------------------
@app.post("/users/me/posts/", response_model=schemas.Post)
def create_post_for_user(
    post: schemas.PostCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    return crud.create_user_post(db=db, post=post, user_id=current_user.id)


# -----------------------------
# 7. 전체 게시물 조회
# -----------------------------
@app.get("/posts/", response_model=List[schemas.Post])
def read_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    posts = crud.get_posts(db, skip=skip, limit=limit)
    return posts


# -----------------------------
# 8. 추천 친구 목록
# -----------------------------
@app.get("/users/me/recommended", response_model=List[schemas.User])
def get_recommended_friends(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    print("현재 로그인된 계정 →", current_user.id, current_user.email, current_user.name)
    recommended = crud.get_recommended_users(db, current_user)
    return recommended


# -----------------------------
# 9. 친구 추가
# -----------------------------
@app.post("/friends/{target_user_id}")
def add_friend(
    target_user_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    crud.add_friend(db, current_user.id, target_user_id)
    return {"message": "친구추가 성공"}


# -----------------------------
# 10. 친구 목록 조회
# -----------------------------
@app.get("/friends/me", response_model=List[schemas.User])
def my_friends(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    return crud.get_my_friends(db, current_user.id)
