import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Playlist(Base):
    __tablename__ = "playlists"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    external_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    snapshot_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    total_tracks: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    playlist_tracks: Mapped[list["PlaylistTrack"]] = relationship(
        back_populates="playlist",
        cascade="all, delete-orphan",
    )


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    external_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    artist_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    album_name: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    duration_ms: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    isrc: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        index=True,
    )

    explicit: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    playlist_tracks: Mapped[list["PlaylistTrack"]] = relationship(
        back_populates="track",
    )


class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"

    __table_args__ = (
        UniqueConstraint(
            "playlist_id",
            "track_id",
            name="uq_playlist_track",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    playlist_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("playlists.id", ondelete="CASCADE"),
        nullable=False,
    )

    track_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tracks.id", ondelete="CASCADE"),
        nullable=False,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    added_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    playlist: Mapped["Playlist"] = relationship(
        back_populates="playlist_tracks"
    )

    track: Mapped["Track"] = relationship(
        back_populates="playlist_tracks"
    )