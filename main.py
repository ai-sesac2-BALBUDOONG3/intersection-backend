# path: main.py
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import models
import schemas
import crud
import security
import ai_service  # 기존 파일 그대로 사용
from database import engine, get_db, check_db_connection

# 1) 테이블 생성 (개발용 빠른 생성)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Intersection / Humane Backend (v1)",
    description="Azure Cosmos DB for PostgreSQL 기반 교집합 친구 찾기 백엔드",
    version="1.0.0",
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# -----------------------------
# 공통 의존성
# -----------------------------
def get_db_session() -> Session:
    yield from get_db()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db_session),
) -> models.User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="출입증(Token)이 유효하지 않습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = security.verify_token(token, credentials_exception)
    login_id: str = payload.get("sub")

    user = crud.get_user_by_login_id(db, login_id=login_id)
    if user is None:
        raise credentials_exception

    return user


# -----------------------------
# Health
# -----------------------------
@app.get("/health", tags=["health"])
def health_root():
    return {"status": "ok", "message": "intersection-backend running"}


@app.get("/health/db", tags=["health"])
def health_db():
    ok = check_db_connection()
    if not ok:
        raise HTTPException(status_code=503, detail="Database connection failed")
    return {"status": "ok", "message": "Database connection successful"}


# -----------------------------
# Root
# -----------------------------
@app.get("/", tags=["root"])
def read_root():
    return {"message": "인터섹션 백엔드 기지에 오신 것을 환영합니다!"}


# -----------------------------
# Auth / Users
# -----------------------------


@app.post("/users/", response_model=schemas.User, tags=["auth"])
def signup(
    body: schemas.UserCreate,
    db: Session = Depends(get_db_session),
):
    # login_id / email 중복 체크
    if crud.get_user_by_login_id(db, body.login_id):
        raise HTTPException(status_code=400, detail="이미 사용 중인 로그인 ID입니다.")
    if body.email and crud.get_user_by_email(db, body.email):
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")

    user = crud.create_user(db, body)
    return user


@app.post("/token", response_model=schemas.Token, tags=["auth"])
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db_session),
):
    # username 필드에 login_id를 받는다고 가정
    user = crud.get_user_by_login_id(db, form_data.username)

    if not user or not security.verify_password(
        form_data.password, user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="로그인 ID 또는 비밀번호가 정확하지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_data = {"sub": user.login_id}
    access_token = security.create_access_token(data=access_token_data)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=schemas.User, tags=["users"])
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user


# -----------------------------
# Profile / School Anchors / Keywords
# -----------------------------


@app.put(
    "/users/me/profile",
    response_model=schemas.UserProfile,
    tags=["profile"],
)
def update_profile(
    body: schemas.UserProfileUpdate,
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user),
):
    profile = crud.upsert_user_profile(db, user_id=current_user.id, profile_in=body)
    return profile


@app.post(
    "/users/me/school-anchors",
    response_model=schemas.UserSchoolAnchor,
    tags=["school"],
)
def add_school_anchor(
    body: schemas.UserSchoolAnchorCreate,
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user),
):
    anchor = crud.create_user_school_anchor(
        db, user_id=current_user.id, anchor_in=body
    )
    return anchor


@app.get(
    "/users/me/school-anchors",
    response_model=List[schemas.UserSchoolAnchor],
    tags=["school"],
)
def list_my_school_anchors(
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user),
):
    anchors = crud.list_user_school_anchors(db, user_id=current_user.id)
    return anchors


@app.post(
    "/users/me/keywords",
    response_model=schemas.UserKeyword,
    tags=["keywords"],
)
def add_keyword(
    body: schemas.UserKeywordCreate,
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user),
):
    kw = crud.add_user_keyword(db, user_id=current_user.id, keyword_in=body)
    return kw


@app.get(
    "/users/me/keywords",
    response_model=List[schemas.UserKeyword],
    tags=["keywords"],
)
def list_keywords(
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user),
):
    kws = crud.list_user_keywords(db, user_id=current_user.id)
    return kws


# -----------------------------
# Institutions (학교 검색)
# -----------------------------


@app.get(
    "/institutions/search",
    response_model=List[schemas.Institution],
    tags=["institutions"],
)
def search_institutions(
    q: Optional[str] = Query(
        None,
        description="학교명 검색어 (부분 일치)",
    ),
    city: Optional[str] = Query(None, description="시/도 (region_city)"),
    district: Optional[str] = Query(None, description="구/군 (region_district)"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db_session),
):
    query = db.query(models.Institution).filter(models.Institution.is_active.is_(True))

    if q:
        like = f"%{q}%"
        query = query.filter(models.Institution.name.ilike(like))

    if city:
        query = query.filter(models.Institution.region_city == city)
    if district:
        query = query.filter(models.Institution.region_district == district)

    institutions = query.order_by(models.Institution.name).limit(limit).all()
    return institutions


# -----------------------------
# Community (간단)
# -----------------------------


@app.post(
    "/communities/",
    response_model=schemas.Community,
    tags=["communities"],
)
def create_community(
    body: schemas.CommunityCreate,
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user),  # 추후 owner 개념 확장 가능
):
    community = crud.create_community(db, body)
    return community


@app.post(
    "/communities/{community_id}/posts",
    response_model=schemas.CommunityPost,
    tags=["community_posts"],
)
def create_community_post(
    community_id: int,
    body: schemas.CommunityPostCreate,
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user),
):
    # body.community_id 를 path 우선으로 강제
    post_in = schemas.CommunityPostCreate(
        community_id=community_id,
        content=body.content,
    )

    # AI 텍스트 심사
    is_safe, message = ai_service.check_text_safety(post_in.content)
    if not is_safe:
        raise HTTPException(status_code=400, detail=message)

    post = crud.create_community_post(db, user_id=current_user.id, post_in=post_in)
    return post


@app.get(
    "/communities/{community_id}/posts",
    response_model=List[schemas.CommunityPost],
    tags=["community_posts"],
)
def list_community_posts(
    community_id: int,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user),
):
    posts = crud.list_community_posts(db, community_id=community_id, limit=limit)
    return posts
