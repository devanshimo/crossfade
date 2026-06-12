"""
app/repositories/user_repository.py
─────────────────────────────────────
Repository: all DB operations for the User model.

Why it exists:
    The repository pattern isolates SQL from business logic.  Services call
    repository methods; if we ever swap PostgreSQL for a different store, only
    repositories change.  It also makes unit-testing services trivial – swap
    the real repo for a fake.

How it connects:
    • Instantiated inside services/spotify.py with an injected AsyncSession.
    • Never imported by route handlers directly.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self._session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def create(self, email: str) -> User:
        user = User(email=email)
        self._session.add(user)
        await self._session.flush()   # populate id without committing
        await self._session.refresh(user)
        return user

    async def get_or_create(self, email: str) -> tuple[User, bool]:
        """
        Return (user, created) where `created` is True if the row is new.

        Using a SELECT-then-INSERT pattern is safe here because:
          1. email has a UNIQUE constraint – a concurrent insert will raise
             IntegrityError which the service layer can catch and retry.
          2. The async session holds a transaction, so we won't see phantom rows.
        """
        user = await self.get_by_email(email)
        if user:
            return user, False
        user = await self.create(email)
        return user, True
