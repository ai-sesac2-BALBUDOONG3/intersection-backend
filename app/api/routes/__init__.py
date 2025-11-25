# app/api/routes/__init__.py

from .health import router as health_router
from .auth import router as auth_router
from .school_histories import router as school_histories_router
from .matching import router as matching_router
from .community import router as communities_router

__all__ = [
    "health_router",
    "auth_router",
    "school_histories_router",
    "matching_router",
    "communities_router",
]
