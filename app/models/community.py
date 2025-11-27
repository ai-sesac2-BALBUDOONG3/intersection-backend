# app/models/community.py
"""
Legacy import shim for community-related models.

The canonical ORM models are defined in app.db.models:
    - models.Community
    - models.CommunityPost
    - models.CommunityComment

This module only re-exports those classes to keep backward compatibility
for code importing from `app.models.community` without creating duplicate
table definitions in SQLAlchemy metadata.
"""

from app.db import models

Community = models.Community
CommunityPost = models.CommunityPost
CommunityComment = models.CommunityComment
