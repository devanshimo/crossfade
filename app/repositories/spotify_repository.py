"""
app/repositories/spotify_repository.py
────────────────────────────────────────
Repository: all DB operations for the SpotifyAccount model.

Why it exists:
    Keeps Spotify-specific persistence separate from the User repository so
    each file has a single reason to change (SRP).

How it connects:
    • Used exclusively by services/spotify.py.
    • Receives an AsyncSession injected at call site.
"""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import SpotifyAccount


class SpotifyAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: uuid.UUID) -> SpotifyAccount | None:
        result = await self._session.execute(
            select(SpotifyAccount).where(SpotifyAccount.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_spotify_user_id(self, spotify_user_id: str) -> SpotifyAccount | None:
        result = await self._session.execute(
            select(SpotifyAccount).where(SpotifyAccount.spotify_user_id == spotify_user_id)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        user_id: uuid.UUID,
        spotify_user_id: str,
        access_token: str,      # already encrypted
        refresh_token: str,     # already encrypted
        token_expiry: datetime,
    ) -> SpotifyAccount:
        """
        Insert a new SpotifyAccount or update an existing one.

        Using a manual upsert (select + create/update) keeps this compatible
        with SQLAlchemy's async session without diving into dialect-specific
        ON CONFLICT syntax.
        """
        account = await self.get_by_user_id(user_id)

        if account is None:
            account = SpotifyAccount(
                user_id=user_id,
                spotify_user_id=spotify_user_id,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expiry=token_expiry,
            )
            self._session.add(account)
        else:
            account.spotify_user_id = spotify_user_id
            account.access_token = access_token
            account.refresh_token = refresh_token
            account.token_expiry = token_expiry

        await self._session.flush()
        await self._session.refresh(account)
        return account
