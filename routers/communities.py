# path: routers/communities.py
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

import crud
import models
import schemas
from deps import get_db_session, get_current_user

router = APIRouter()


@router.post(
    "/communities/",
    response_model=schemas.Community,
    tags=["communities"],
)
def create_community(
    body: schemas.CommunityCreate,
    db: Session = Depends(get_db_session),
    current_user: models.User = Depends(get_current_user),  # 추후 owner 개념 확장 가능
):
    """커뮤니티 생성 (예: 같은 학교/기수 방)."""
    community = crud.create_community(db, body)
    return community


@router.post(
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
    """
    커뮤니티 게시글 작성.
    (콘텐츠 안전 검사는 현재 사용하지 않음)
    """
    # body.community_id 를 path 우선으로 강제
    post_in = schemas.CommunityPostCreate(
        community_id=community_id,
        content=body.content,
    )

    post = crud.create_community_post(db, user_id=current_user.id, post_in=post_in)
    return post


@router.get(
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
    """커뮤니티 게시글 목록 조회."""
    posts = crud.list_community_posts(db, community_id=community_id, limit=limit)
    return posts
