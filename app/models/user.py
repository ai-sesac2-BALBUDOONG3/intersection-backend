# app/models/user.py
"""
Legacy import shim for User model.

To avoid defining the 'users' table twice in SQLAlchemy metadata,
this module simply re-exports the canonical User ORM model
defined in app.db.models.

New code SHOULD import from `app.db.models` directly:
    from app.db import models
    user = models.User(...)

Existing code that does:
    from app.models.user import User
will continue to work, but no longer creates a second table definition.
"""

from app.db import models

User = models.User
