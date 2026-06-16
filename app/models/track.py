from sqlalchemy import Column, String, DateTime, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db.base import Base


class Track(Base):
    __tablename__ = "tracks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    spotify_id = Column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )

    name = Column(
        String,
        nullable=False,
    )

    artist_names = Column(
        String,
        nullable=False,
    )

    album_name = Column(
        String,
        nullable=True,
    )

    duration_ms = Column(
        Integer,
        nullable=True,
    )

    isrc = Column(
        String,
        nullable=True,
        index=True,
    )

    apple_music_id = Column(
        String,
        nullable=True,
        index=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    playlist_tracks = relationship(
        "PlaylistTrack",
        back_populates="track",
        cascade="all, delete-orphan",
    )
