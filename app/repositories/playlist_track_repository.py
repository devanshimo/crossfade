import uuid
from typing import Optional, Sequence

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.playlist_track import PlaylistTrack


class PlaylistTrackRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        playlist_id: uuid.UUID,
        track_id: uuid.UUID,
        position: int,
        added_at=None,
        added_by_spotify_id: Optional[str] = None,
    ) -> PlaylistTrack:
        playlist_track = PlaylistTrack(
            playlist_id=playlist_id,
            track_id=track_id,
            position=position,
            added_at=added_at,
            added_by_spotify_id=added_by_spotify_id,
        )
        self.session.add(playlist_track)
        await self.session.flush()
        return playlist_track

    async def bulk_create(
        self, playlist_id: uuid.UUID, entries: Sequence[dict]
    ) -> Sequence[PlaylistTrack]:
        playlist_tracks = []

        for entry in entries:
            playlist_tracks.append(
                PlaylistTrack(
                    playlist_id=playlist_id,
                    track_id=entry["track_id"],
                    position=entry["position"],
                    added_at=entry.get("added_at"),
                    added_by_spotify_id=entry.get("added_by_spotify_id"),
                )
            )

        self.session.add_all(playlist_tracks)
        await self.session.flush()
        return playlist_tracks

    async def delete_for_playlist(self, playlist_id: uuid.UUID) -> None:
        await self.session.execute(
            delete(PlaylistTrack).where(PlaylistTrack.playlist_id == playlist_id)
        )
        await self.session.flush()