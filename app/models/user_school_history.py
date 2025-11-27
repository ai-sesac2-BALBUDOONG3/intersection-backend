# app/models/user_school_history.py
"""
Legacy import shim for UserSchoolHistory model.

The canonical ORM model is defined in app.db.models.UserSchoolHistory.
This module only re-exports that class to keep backward compatibility
for code importing from `app.models.user_school_history`.
"""

from app.db import models

UserSchoolHistory = models.UserSchoolHistory
