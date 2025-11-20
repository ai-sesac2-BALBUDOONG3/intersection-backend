# path: routers/__init__.py
from . import health, auth, users, institutions, communities, internal, matching

__all__ = [
    "health",
    "auth",
    "users",
    "institutions",
    "communities",
    "internal",
    "matching",
]
