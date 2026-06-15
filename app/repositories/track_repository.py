import uuid
from typing import Optional, Sequence

from app.models import Track
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.track import Track


class TrackRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_spotify_id(self, spotify_id: str) -> Optional[Track]:
        result = await self.session.execute(
            select(Track).where(Track.spotify_id == spotify_id)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        spotify_id: str,
        name: str,
        artist_names: str,
        album_name: str,
        duration_ms: int,
    ) -> Track:
        track = await self.get_by_spotify_id(spotify_id)

        if track is None:
            track = Track(
                spotify_id=spotify_id,
                name=name,
                artist_names=artist_names,
                album_name=album_name,
                duration_ms=duration_ms,
            )
            self.session.add(track)
        else:
            track.name = name
            track.artist_names = artist_names
            track.album_name = album_name
            track.duration_ms = duration_ms

        await self.session.flush()
        return track

    async def bulk_upsert(self, tracks_data: Sequence[dict]) -> Sequence[Track]:
        spotify_ids = [t["spotify_id"] for t in tracks_data]

        result = await self.session.execute(
            select(Track).where(Track.spotify_id.in_(spotify_ids))
        )
        existing = {t.spotify_id: t for t in result.scalars().all()}

        ordered_tracks = []

        for data in tracks_data:
            track = existing.get(data["spotify_id"])

            if track is None:
                track = Track(
                    
                spotify_id=data["spotify_id"],
                name=data["name"],
                artist_names=data["artist_names"],
                album_name=data["album_name"],
                duration_ms=data["duration_ms"],

            )
                self.session.add(track)
                existing[data["spotify_id"]] = track
            else:
                track.name = data["name"]
                track.artist_names = data["artist_names"]
                track.album_name = data["album_name"]
                track.duration_ms = data["duration_ms"]
                
            ordered_tracks.append(track)

        await self.session.flush()
        return ordered_tracks