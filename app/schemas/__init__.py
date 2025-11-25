# app/schemas/__init__.py

from .auth import (
    UserRead,
    UserRegisterRequest,
    UserLoginRequest,
    Token,
)
from .school_history import (
    UserSchoolHistoryCreate,
    UserSchoolHistoryRead,
)
from .matching import (
    MatchCandidateRead,
    MatchCandidateWithExplanationRead,
)
from .community import (
    CommunityCreate,
    CommunityRead,
    CommunityPostCreate,
    CommunityPostRead,
    CommunityCommentCreate,
    CommunityCommentRead,
)

__all__ = [
    "UserRead",
    "UserRegisterRequest",
    "UserLoginRequest",
    "Token",
    "UserSchoolHistoryCreate",
    "UserSchoolHistoryRead",
    "MatchCandidateRead",
    "MatchCandidateWithExplanationRead",
    "CommunityCreate",
    "CommunityRead",
    "CommunityPostCreate",
    "CommunityPostRead",
    "CommunityCommentCreate",
    "CommunityCommentRead",
]
