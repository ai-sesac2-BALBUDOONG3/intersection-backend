# app/api/routes/__init__.py

from .health import router as health_router
from .auth import router as auth_router
from .institutions import router as institutions_router
from .users import router as users_router
from .school_histories import router as school_histories_router
from .matching import router as matching_router
from .community import router as communities_router  # ★ 여기 community 로 import
from .anchors import router as anchors_router
from .friends import router as friends_router  # ★ 신규 추가

__all__ = [
    "health_router",
    "auth_router",
    "institutions_router",
    "users_router",
    "school_histories_router",
    "matching_router",
    "communities_router",
    "anchors_router",
    "friends_router",  # ★ 신규 추가
]
