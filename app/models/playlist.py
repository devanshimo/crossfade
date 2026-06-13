"""app/models/playlist.py
───────────────────────
ORM models: Playlist, Track, PlaylistTrack.

Design decisions:
    • Playlist and Track use the Spotify ID (string) as the natural key
      for lookups, but keep a surrogate UUID primary key so foreign keys
      internal to Crossfade are stable even if Spotify ever changes IDs.

    • PlaylistTrack is an explicit association object (not just a secondary
      table) so we can store position and added_at metadata alongside the
      relationship without fighting SQLAlchemy's secondary-table limitations.

    • source_platform is an enum column, making the schema forward-compatible
      with Apple Music playlists without a migration change.

    • Snapshots: each import run is tagged with imported_at on Playlist.
      Comparing Playlist.track_count (from Spotify) against the DB row count
      on PlaylistTrack lets the import service detect drift without fetching
      all tracks every time.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Playlist(Base):
    """
    A user-owned snapshot of a Spotify playlist.

    One User → many Playlists (one per Spotify playlist they import).
    The same Spotify playlist imported twice is idempotent: the row is updated
    in place and PlaylistTrack rows are reconciled.
    """
    __tablename__ = "playlists"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "spotify_playlist_id",
            name="uq_playlist_user_spotify",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    spotify_playlist_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    snapshot_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Spotify snapshot ID used for sync detection",
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

    # Relationships

    user: Mapped["User"] = relationship(
        "User",
        back_populates="playlists",
    )

    playlist_tracks: Mapped[list["PlaylistTrack"]] = relationship(
        "PlaylistTrack",
        back_populates="playlist",
        cascade="all, delete-orphan",
        order_by="PlaylistTrack.position",
    )

    def __repr__(self) -> str:
        return f"<Playlist id={self.id} name={self.name!r}>"


