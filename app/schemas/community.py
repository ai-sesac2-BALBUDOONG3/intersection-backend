# app/schemas/community.py

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# --------- 커뮤니티 ---------


class CommunityBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_private: bool = False


class CommunityCreate(CommunityBase):
    pass


class CommunityRead(CommunityBase):
    id: int
    created_by_user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --------- 게시글 ---------


class CommunityPostBase(BaseModel):
    title: str
    content: str


class CommunityPostCreate(CommunityPostBase):
    pass


class CommunityPostRead(CommunityPostBase):
    id: int
    community_id: int
    author_user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --------- 댓글 ---------


class CommunityCommentBase(BaseModel):
    content: str
    parent_comment_id: Optional[int] = None


class CommunityCommentCreate(CommunityCommentBase):
    pass


class CommunityCommentRead(CommunityCommentBase):
    id: int
    post_id: int
    author_user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
