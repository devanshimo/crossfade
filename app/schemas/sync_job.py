import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.sync_job import SyncJobStatus


class SyncJobRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    playlist_id: uuid.UUID
    status: SyncJobStatus
    total_tracks: int
    matched_tracks: int
    synced_tracks: int
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SyncJobCreateResponse(BaseModel):
    id: uuid.UUID
    status: SyncJobStatus