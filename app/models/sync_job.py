import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SAEnum
from sqlalchemy import Integer

from app.db.base import Base


class SyncJobStatus(PyEnum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class SyncJob(Base):
    __tablename__ = "sync_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    playlist_id = Column(UUID(as_uuid=True), ForeignKey("playlists.id"), nullable=False, index=True)
    status = Column(SAEnum(SyncJobStatus), nullable=False, default=SyncJobStatus.pending)
    total_tracks = Column(Integer, nullable=False, default=0)
    matched_tracks = Column(Integer, nullable=False, default=0)
    synced_tracks = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", lazy="noload")
    playlist = relationship("Playlist", lazy="noload")