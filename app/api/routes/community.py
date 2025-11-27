# app/api/routes/communities.py

from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)
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

# ============================================================
# 커뮤니티 영역
#   - Intersection 컨셉: 학교 / 지역 / 시기 기반 소통 공간
#   - 지금은 범용 커뮤니티 구조 + Intersection 기획과 호환되게 설계
# ============================================================


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
) -> CommunityRead:
    """
    새로운 커뮤니티 생성.

    Intersection 컨셉에서는 예를 들어 아래처럼 사용할 수 있음:
    - 학교 기반: "강동중학교 08~10 동기방"
    - 지역 기반: "서울 강동구 천호동 동네방"
    - 프리: "기억 조각 수다방"
    """
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
) -> List[CommunityRead]:
    """
    전체 커뮤니티 목록 조회.

    - 추후: 학교/지역/시기 기반 필터를 붙여서
      Intersection 컨셉에 맞게 '나와 관련 있는 커뮤니티'만 보여줄 수 있음.
    """
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
) -> CommunityRead:
    community = db.query(Community).filter(Community.id == community_id).first()
    if not community:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="커뮤니티를 찾을 수 없습니다.",
        )
    return CommunityRead.model_validate(community)


@router.get(
    "/me/joined",
    response_model=List[CommunityRead],
    summary="내가 활동 중인 커뮤니티 목록",
)
def list_my_communities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[CommunityRead]:
    """
    내가 작성한 게시글이 있는 커뮤니티 목록.

    - Intersection 컨셉에서 '내가 발자국 남긴 공간' 리스트로 활용 가능.
    """
    # 내가 쓴 게시글이 있는 커뮤니티 id들 조회
    subq = (
        db.query(CommunityPost.community_id)
        .filter(
            CommunityPost.author_user_id == current_user.id,
            CommunityPost.is_deleted == False,  # noqa: E712
        )
        .distinct()
        .subquery()
    )

    communities = db.query(Community).filter(Community.id.in_(subq)).all()
    return [CommunityRead.model_validate(c) for c in communities]


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
) -> CommunityPostRead:
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
) -> List[CommunityPostRead]:
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


@router.delete(
    "/posts/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="내 게시글 삭제 (소프트 삭제)",
)
def delete_post(
    post_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    내 게시글을 소프트 삭제(is_deleted=True) 한다.
    """
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post or post.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글을 찾을 수 없습니다.",
        )

    if post.author_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인이 작성한 게시글만 삭제할 수 있습니다.",
        )

    post.is_deleted = True
    db.add(post)
    db.commit()
    return None


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
) -> CommunityCommentRead:
    post = (
        db.query(CommunityPost)
        .filter(
            CommunityPost.id == post_id,
            CommunityPost.is_deleted == False,  # noqa: E712
        )
        .first()
    )
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
) -> List[CommunityCommentRead]:
    post = (
        db.query(CommunityPost)
        .filter(
            CommunityPost.id == post_id,
            CommunityPost.is_deleted == False,  # noqa: E712
        )
        .first()
    )
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


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="내 댓글 삭제 (소프트 삭제)",
)
def delete_comment(
    comment_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    내 댓글을 소프트 삭제(is_deleted=True) 한다.
    """
    comment = (
        db.query(CommunityComment)
        .filter(CommunityComment.id == comment_id)
        .first()
    )
    if not comment or comment.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="댓글을 찾을 수 없습니다.",
        )

    if comment.author_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인이 작성한 댓글만 삭제할 수 있습니다.",
        )

    comment.is_deleted = True
    db.add(comment)
    db.commit()
    return None
