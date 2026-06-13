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
 
    async def create(self, email: str, display_name: str | None = None) -> User:
        user = User(email=email, display_name=display_name)
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user
 
    async def get_or_create(
        self,
        email: str,
        display_name: str | None = None,   # [Day 2]
    ) -> tuple[User, bool]:
        """
        Return (user, created).
 
        [Day 2] For returning users, update display_name if Spotify reports a
        new value – keeps the UI name fresh without extra round-trips.
        """
        user = await self.get_by_email(email)
        if user:
            if display_name and user.display_name != display_name:
                user.display_name = display_name
                await self._session.flush()
                await self._session.refresh(user)
            return user, False
        user = await self.create(email, display_name=display_name)
        return user, True
 