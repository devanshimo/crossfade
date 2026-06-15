import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class PlaylistImportRequest(BaseModel):
    spotify_playlist_id: str


class PlaylistImportResponse(BaseModel):
    playlist_id: uuid.UUID
    playlist_name: str
    tracks_imported: int


class TrackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    spotify_id: str
    name: str
    artist_names: str
    album_name: Optional[str] = None
    duration_ms: Optional[int] = None


class PlaylistRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    spotify_playlist_id: str
    name: str
    description: Optional[str] = None
    snapshot_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    tracks: List[TrackRead] = []
class PlaylistListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    spotify_playlist_id: str
    name: str
    description: Optional[str] = None
    snapshot_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    track_count: int