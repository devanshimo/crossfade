"""
app/db/base.py
───────────────
SQLAlchemy 2.0 declarative base shared by all models.

Why it exists:
    Every model must inherit from the same `Base`.  A single module prevents
    circular imports: models import Base from here, Alembic's env.py imports
    Base from here, and the session factory never needs to know about models.

How it connects:
    • All models in app/models/ inherit from Base.
    • alembic/env.py imports Base.metadata for autogenerate support.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass
