# app/api/routes/communities.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.community import Community, CommunityPost, CommunityComment
from app.models.user import User
from app.schemas.community import (
    CommunityCreate,
    CommunityRead,
    CommunityPostCreate,
    CommunityPostRead,
    CommunityCommentCreate,
    CommunityCommentRead,
)

router = APIRouter(
    prefix="/communities",
    tags=["communities"],
)


# --------- 커뮤니티 ---------


@router.post(
    "",
    response_model=CommunityRead,
    status_code=status.HTTP_201_CREATED,
    summary="커뮤니티 생성",
)
def create_community(
    payload: CommunityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    community = Community(
        name=payload.name,
        description=payload.description,
        is_private=payload.is_private,
        created_by_user_id=current_user.id,
    )
    db.add(community)
    db.commit()
    db.refresh(community)
    return CommunityRead.model_validate(community)


@router.get(
    "",
    response_model=List[CommunityRead],
    summary="커뮤니티 목록 조회",
)
def list_communities(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    # 일단은 공개/비공개 구분 없이 전부 노출 (추후 권한 로직 추가 가능)
    communities = (
        db.query(Community)
        .order_by(Community.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [CommunityRead.model_validate(c) for c in communities]


@router.get(
    "/{community_id}",
    response_model=CommunityRead,
    summary="커뮤니티 단건 조회",
)
def get_community(
    community_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="커뮤니티를 찾을 수 없습니다.",
        )
    return CommunityRead.model_validate(community)


# --------- 게시글 ---------


@router.post(
    "/{community_id}/posts",
    response_model=CommunityPostRead,
    status_code=status.HTTP_201_CREATED,
    summary="커뮤니티 글 작성",
)
def create_post(
    community_id: int = Path(..., ge=1),
    payload: CommunityPostCreate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="커뮤니티를 찾을 수 없습니다.",
        )

    post = CommunityPost(
        community_id=community_id,
        author_user_id=current_user.id,
        title=payload.title,
        content=payload.content,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return CommunityPostRead.model_validate(post)


@router.get(
    "/{community_id}/posts",
    response_model=List[CommunityPostRead],
    summary="커뮤니티 글 목록 조회",
)
def list_posts(
    community_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="커뮤니티를 찾을 수 없습니다.",
        )

    posts = (
        db.query(CommunityPost)
        .filter(
            CommunityPost.community_id == community_id,
            CommunityPost.is_deleted == False,  # noqa: E712
        )
        .order_by(CommunityPost.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [CommunityPostRead.model_validate(p) for p in posts]


# --------- 댓글 ---------


@router.post(
    "/posts/{post_id}/comments",
    response_model=CommunityCommentRead,
    status_code=status.HTTP_201_CREATED,
    summary="댓글 작성",
)
def create_comment(
    post_id: int = Path(..., ge=1),
    payload: CommunityCommentCreate = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(CommunityPost).filter(
        CommunityPost.id == post_id,
        CommunityPost.is_deleted == False,  # noqa: E712
    ).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글을 찾을 수 없습니다.",
        )

    comment = CommunityComment(
        post_id=post_id,
        author_user_id=current_user.id,
        content=payload.content,
        parent_comment_id=payload.parent_comment_id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return CommunityCommentRead.model_validate(comment)


@router.get(
    "/posts/{post_id}/comments",
    response_model=List[CommunityCommentRead],
    summary="댓글 목록 조회",
)
def list_comments(
    post_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    post = db.query(CommunityPost).filter(
        CommunityPost.id == post_id,
        CommunityPost.is_deleted == False,  # noqa: E712
    ).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글을 찾을 수 없습니다.",
        )

    comments = (
        db.query(CommunityComment)
        .filter(
            CommunityComment.post_id == post_id,
            CommunityComment.is_deleted == False,  # noqa: E712
        )
        .order_by(CommunityComment.created_at.asc())
        .all()
    )

    return [CommunityCommentRead.model_validate(c) for c in comments]
