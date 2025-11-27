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
    MatchScoreBreakdown,
    MatchRecommendation,
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
    # auth
    "UserRead",
    "UserRegisterRequest",
    "UserLoginRequest",
    "Token",
    # school history
    "UserSchoolHistoryCreate",
    "UserSchoolHistoryRead",
    # matching
    "MatchScoreBreakdown",
    "MatchRecommendation",
    # community
    "CommunityCreate",
    "CommunityRead",
    "CommunityPostCreate",
    "CommunityPostRead",
    "CommunityCommentCreate",
    "CommunityCommentRead",
]
