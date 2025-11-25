from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse # 👈 카카오 리다이렉트를 위해 추가
from urllib.parse import urlencode # 👈 URL 인코딩을 위해 추가
import httpx # 👈 카카오 API 통신을 위해 추가
import os 
import logging 

import models
import schemas
import crud
import security
from database import SessionLocal, engine

# 로깅 설정
logging.basicConfig(level=logging.INFO)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ⚠️ ⭐️ 카카오 API 설정 (복사한 키 적용 완료) ⭐️
KAKAO_REST_API_KEY = "bb1f874b622f79c88cce8a1b4080bb61"
KAKAO_REDIRECT_URI = "http://127.0.0.1:8000/auth/kakao/callback"
# -----------------------------------------------------------------------


@app.get("/")
def read_root():
    return {"message": "인터섹션 백엔드 기지에 오신 것을 환영합니다!"}

# 1. 회원가입
@app.post("/users/", response_model=schemas.User)
def create_user_endpoint(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user_data.email)
    if db_user:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")
    new_user = crud.create_user(db=db, user=user_data)
    return new_user

# 2. 로그인 (일반)
@app.post("/token", response_model=schemas.Token)
def login_for_access_token(login_data: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=login_data.email)
    if not user or not security.verify_password(login_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다.")
    
    token_data = {"sub": user.email}
    access_token = security.create_access_token(data=token_data)
    return {"access_token": access_token, "token_type": "bearer"}

# 3. 현재 유저 확인
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401, detail="자격 증명이 유효하지 않습니다.", headers={"WWW-Authenticate": "Bearer"}
    )
    payload = security.verify_token(token, credentials_exception)
    email: str = payload.get("sub")
    user = crud.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

# 4. 추가 정보 입력
@app.post("/users/me/details", response_model=schemas.UserDetail)
def create_details_endpoint(detail_data: schemas.UserDetailCreate, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    return crud.create_user_detail(db=db, detail=detail_data, user_id=current_user.id)

# 5. 내 정보 조회
@app.get("/users/me", response_model=schemas.User)
def read_users_me(current_user: schemas.User = Depends(get_current_user)):
    return current_user

# 6. 게시글 작성
@app.post("/users/me/posts/", response_model=schemas.Post)
def create_post_for_user(post: schemas.PostCreate, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    return crud.create_user_post(db=db, post=post, user_id=current_user.id)

# 7. 게시글 목록
@app.get("/posts/", response_model=List[schemas.Post])
def read_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_posts(db, skip=skip, limit=limit)

# 8. 친구 추천
@app.get("/users/me/recommended", response_model=List[schemas.User])
def get_recommended_friends(db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    return crud.get_recommended_users(db, current_user)

# 9. 친구 추가
@app.post("/friends/{target_user_id}")
def add_friend(target_user_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    crud.add_friend(db, current_user.id, target_user_id)
    return {"message": "친구추가 성공"}

# 10. 내 친구 목록
@app.get("/friends/me", response_model=List[schemas.User])
def my_friends(db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    return crud.get_my_friends(db, current_user.id)

# --- [새로 추가된 기능] ---

# 11. 게시글 수정
@app.put("/posts/{post_id}", response_model=schemas.Post)
def update_post_endpoint(post_id: int, post_update: schemas.PostUpdate, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    updated_post = crud.update_post(db, post_id, post_update, current_user.id)
    if updated_post is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if updated_post == "not_owner":
        raise HTTPException(status_code=403, detail="작성자만 수정할 수 있습니다.")
    return updated_post

# 12. 게시글 삭제
@app.delete("/posts/{post_id}")
def delete_post_endpoint(post_id: int, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    result = crud.delete_post(db, post_id, current_user.id)
    if result is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if result == "not_owner":
        raise HTTPException(status_code=403, detail="작성자만 삭제할 수 있습니다.")
    return {"message": "삭제되었습니다."}

# 13. 댓글 작성
@app.post("/posts/{post_id}/comments", response_model=schemas.Comment)
def create_comment_endpoint(post_id: int, comment: schemas.CommentCreate, db: Session = Depends(get_db), current_user: schemas.User = Depends(get_current_user)):
    return crud.create_comment(db, comment, current_user.id, post_id)

# 14. 댓글 조회
@app.get("/posts/{post_id}/comments", response_model=List[schemas.Comment])
def read_comments_endpoint(post_id: int, db: Session = Depends(get_db)):
    return crud.get_comments_by_post(db, post_id)


# --------------------------------------------------------------------
# ⭐️ [ 카카오 로그인 기능 ] ⭐️
# --------------------------------------------------------------------

# 15. 카카오 로그인 페이지로 이동
@app.get("/auth/kakao/login")
async def kakao_login():
    """사용자를 카카오 로그인 페이지로 리다이렉트합니다."""
    
    params = {
        "client_id": KAKAO_REST_API_KEY,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "response_type": "code",
    }
    kakao_auth_url = "https://kauth.kakao.com/oauth/authorize?" + urlencode(params)
    
    # RedirectResponse를 사용하여 사용자를 카카오 로그인 창으로 보냅니다.
    return RedirectResponse(kakao_auth_url)


# 16. 카카오의 응답(콜백) 처리
@app.get("/auth/kakao/callback", response_model=schemas.Token)
async def kakao_callback(code: str, db: Session = Depends(get_db)):
    """카카오로부터 인가 코드를 받아 토큰을 교환하고 사용자 정보를 처리합니다."""
    
    # 1. 인가 코드를 사용하여 접근 토큰 요청 (카카오 API 호출)
    token_url = "https://kauth.kakao.com/oauth/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": KAKAO_REST_API_KEY,
        "redirect_uri": KAKAO_REDIRECT_URI,
        "code": code,
    }
    
    async with httpx.AsyncClient() as client:
        token_response = await client.post(token_url, data=token_data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        token_info = token_response.json()
    
    if "error" in token_info:
        logging.error(f"Kakao Token Exchange Failed: {token_info}")
        raise HTTPException(status_code=400, detail=f"카카오 토큰 교환 실패: {token_info.get('error_description', '알 수 없는 오류')}")

    access_token = token_info.get("access_token")

    # 2. 접근 토큰으로 사용자 정보 요청 (카카오 API 호출)
    user_info_url = "https://kapi.kakao.com/v2/user/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with httpx.AsyncClient() as client:
        user_response = await client.get(user_info_url, headers=headers)
        user_info = user_response.json()
        
    # 3. 핵심 데이터 추출 및 DB 처리
    kakao_id = str(user_info.get("id"))
    kakao_account = user_info.get("kakao_account", {})
    profile = kakao_account.get("profile", {})
    email = kakao_account.get("email") # 이메일 동의를 받아야 함
    nickname = profile.get("nickname", "카카오사용자")
    
    # 기존 사용자 확인
    db_user = crud.get_user_by_kakao_id(db, kakao_id)
    
    if not db_user:
        # 최초 로그인: 회원가입 처리 (crud.py에서 정의된 함수 사용)
        db_user = crud.create_social_user(db, kakao_id, nickname, email)
        
    # 4. 서버 자체 JWT 토큰 발급 및 반환 (로그인 성공)
    token_data = {"sub": db_user.email} 
    server_access_token = security.create_access_token(data=token_data)
    
    return {"access_token": server_access_token, "token_type": "bearer"}