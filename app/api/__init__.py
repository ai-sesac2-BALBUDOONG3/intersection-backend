# app/api/__init__.py

from app.api.routes import (
    health_router,
    auth_router,
    school_histories_router,
    matching_router,
    communities_router,
)

__all__ = [
    "health_router",
    "auth_router",
    "school_histories_router",
    "matching_router",
    "communities_router",
]
