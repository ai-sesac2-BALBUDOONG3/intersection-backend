from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List # 리스트 형태 출력을 위해 필요

# 우리가 만든 부품들 가져오기
import models
import schemas
import crud
import security
import ai_service 
from database import SessionLocal, engine

# [ 1. 서버 실행 시, '창고'에 테이블 생성 ]
models.Base.metadata.create_all(bind=engine)

# [ 2. FastAPI '본체' 생성 ]
app = FastAPI()

# [ 3. '자동 검사기' 설치 (토큰 주소 알려주기) ]
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# --- [ '자동문' 기능 (DB 세션 관리) ] ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- [ 기본 환영 메시지 ] ---
@app.get("/")
def read_root():
    return {"message": "인터섹션 백엔드 기지에 오신 것을 환영합니다!"}


# --- [ 1. 회원가입 창구 (업그레이드 완료!) ] ---
@app.post("/users/", response_model=schemas.User)
def create_user_endpoint(
    user_data: schemas.UserCreate, # 명세서대로 늘어난 신청서 양식을 받습니다.
    db: Session = Depends(get_db)
):
    # 1. 중복 이메일 검사
    db_user = crud.get_user_by_email(db, email=user_data.email)
    if db_user:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
    
    # 2. 신규 회원 등록 (직원에게 신청서 통째로 전달)
    new_user = crud.create_user(db=db, user=user_data)
    
    return new_user


# --- [ 2. 로그인 창구 (출입증 발급) ] ---
@app.post("/token", response_model=schemas.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # 1. 회원 조회 (username=이메일)
    user = crud.get_user_by_email(db, email=form_data.username)
    
    # 2. 아이디/비번 확인
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="이메일 또는 비밀번호가 정확하지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 3. 출입증(Token) 발급
    access_token_data = {"sub": user.email}
    access_token = security.create_access_token(data=access_token_data)
    
    return {"access_token": access_token, "token_type": "bearer"}


# --- [ 3. '현재 로그인한 회원' 자동 확인 함수 ] ---
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="출입증(Token)이 유효하지 않습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 토큰 검증
    payload = security.verify_token(token, credentials_exception)
    email: str = payload.get("sub")
    
    # 회원 정보 가져오기
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
        
    return user


# --- [ 4. 내 정보 보기 (회원 전용) ] ---
@app.get("/users/me", response_model=schemas.User)
def read_users_me(
    current_user: schemas.User = Depends(get_current_user)
):
    return current_user


# --- [ 5. 글쓰기 창구 (AI 심사 기능 포함!) ] ---
@app.post("/users/me/posts/", response_model=schemas.Post)
def create_post_for_user(
    post: schemas.PostCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(get_current_user)
):
    # [ 🤖 1단계: AI 심사위원에게 검사받기 ]
    is_safe, message = ai_service.check_text_safety(post.content)
    
    # [ 🚨 2단계: 심사 탈락 시 ]
    if not is_safe:
        raise HTTPException(status_code=400, detail=message)
    
    # [ ✅ 3단계: 심사 통과 시 저장 ]
    return crud.create_user_post(db=db, post=post, user_id=current_user.id)


# --- [ 6. 전체 글 목록 보기 ] ---
@app.get("/posts/", response_model=List[schemas.Post])
def read_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    posts = crud.get_posts(db, skip=skip, limit=limit)
    return posts