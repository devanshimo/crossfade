"""
app/models/user.py
───────────────────
SQLAlchemy ORM models: User and SpotifyAccount.

Why it exists:
    Separating models by domain (user, playlist, …) keeps each file focused
    and avoids a monolithic models.py that grows unwieldy as the schema grows.

How it connects:
    • Repositories read/write these via AsyncSession.
    • Alembic autogenerates migrations from their metadata (via db/base.py).
    • Schemas (Pydantic) mirror these for serialisation but are kept separate
      to avoid coupling the API contract to the DB schema.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    """
    Platform-level user.

    One User can have one SpotifyAccount (and later one AppleMusicAccount).
    The email is the stable identifier across OAuth providers.
    """

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    display_name: Mapped[str | None] = mapped_column(
    String(255),
    nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),
    onupdate=func.now(),
    nullable=False,
    )


    # ── Relationships ─────────────────────────────────────────────────────────
    spotify_account: Mapped["SpotifyAccount | None"] = relationship(
        "SpotifyAccount",
        back_populates="user",
        uselist=False,          # one-to-one
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"


class SpotifyAccount(Base):
    """
    Stores the OAuth credentials for a Spotify account linked to a User.

    Tokens are stored **encrypted** (see core/security.py).  The raw values
    here are the ciphertext strings; the service layer handles enc/dec.
    """

    __tablename__ = "spotify_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,    # one Spotify account per platform user
        nullable=False,
        index=True,
    )
    spotify_user_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Spotify's own user ID (e.g. '31xyz...')",
    )
    # Stored as Fernet-encrypted ciphertext
    access_token: Mapped[str] = mapped_column(String(1024), nullable=False)
    refresh_token: Mapped[str] = mapped_column(String(1024), nullable=False)
    token_expiry: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="UTC datetime when the access_token expires",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="spotify_account")

    def __repr__(self) -> str:
        return f"<SpotifyAccount id={self.id} spotify_user_id={self.spotify_user_id}>"
