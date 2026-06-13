"""
app/schemas/user.py
────────────────────
Pydantic v2 schemas for User and SpotifyAccount.

Why it exists:
    The ORM models are the DB truth; schemas are the API contract.  Keeping
    them separate means we can freely add internal DB columns (soft-delete
    flags, internal counters) without leaking them to callers, and rename API
    fields without touching migrations.

How it connects:
    • api/v1/endpoints/auth.py – returns these from route handlers.
    • services/spotify.py      – returns SpotifyProfileResponse from Spotify API.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


# ── User ──────────────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    email: EmailStr


class UserRead(UserBase):
    """Public-facing user representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    display_name: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


# ── Spotify Account ───────────────────────────────────────────────────────────

class SpotifyAccountRead(BaseModel):
    """Spotify linkage info safe to return to the user (no tokens)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    spotify_user_id: str
    token_expiry: datetime
    created_at: datetime


# ── Auth response ─────────────────────────────────────────────────────────────

class AuthenticatedUser(BaseModel):
    """
    Returned by GET /auth/spotify/callback and GET /auth/spotify/me.

    Bundles the platform user record with their linked Spotify account so
    the frontend has everything it needs in one round trip.
    """

    user: UserRead
    spotify_account: SpotifyAccountRead
    access_token: str           # our own internal JWT, not Spotify's
    token_type: str = "bearer"


# ── Spotify raw profile (internal) ───────────────────────────────────────────

class SpotifyUserProfile(BaseModel):
    """
    Mirrors the subset of Spotify's /v1/me response we care about.
    Not exposed publicly – used internally between service and repository.
    """

    id: str                     # Spotify user ID
    email: str
    display_name: str | None = None

class CurrentUserResponse(BaseModel):
    user: UserRead
    spotify_account: SpotifyAccountRead
