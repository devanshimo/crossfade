from unittest import result
import uuid
from typing import Optional, Sequence

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.playlist import Playlist
from app.models.track import Track
from app.models.playlist_track import PlaylistTrack


class PlaylistRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_user_spotify_id(
        self, user_id: uuid.UUID, spotify_playlist_id: str
    ) -> Optional[Playlist]:
        result = await self.session.execute(
            select(Playlist).where(
                Playlist.user_id == user_id,
                Playlist.spotify_playlist_id == spotify_playlist_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: uuid.UUID) -> Sequence[Playlist]:
        result = await self.session.execute(
            select(Playlist).where(Playlist.user_id == user_id)
        )
        return result.scalars().all()
    async def get_by_id(
    self,
    playlist_id: uuid.UUID,
) -> Optional[Playlist]:
        result = await self.session.execute(
        select(Playlist).where(
            Playlist.id == playlist_id
        )
    )

        return result.scalar_one_or_none()

    async def get_with_tracks(
        self, playlist_id: uuid.UUID
    ) -> Optional[Playlist]:
        result = await self.session.execute(
            select(Playlist)
            .where(Playlist.id == playlist_id)
            .options(
                selectinload(Playlist.playlist_tracks).selectinload(
                    PlaylistTrack.track
                )
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        user_id: uuid.UUID,
        spotify_playlist_id: str,
        name: str,
        description: Optional[str],
        snapshot_id: Optional[str],
    ) -> Playlist:
        playlist = await self.get_by_user_spotify_id(user_id, spotify_playlist_id)

        if playlist is None:
            playlist = Playlist(
                user_id=user_id,
                spotify_playlist_id=spotify_playlist_id,
                name=name,
                description=description,
                snapshot_id=snapshot_id,
            )
            self.session.add(playlist)
        else:
            playlist.name = name
            playlist.description = description
            playlist.snapshot_id = snapshot_id

        await self.session.flush()
        return playlist

    async def replace_tracks(
        self,
        playlist_id: uuid.UUID,
        ordered_tracks: Sequence[dict],
    ) -> None:
        await self.session.execute(
            delete(PlaylistTrack).where(PlaylistTrack.playlist_id == playlist_id)
        )

        for entry in ordered_tracks:
            self.session.add(
                PlaylistTrack(
                    playlist_id=playlist_id,
                    track_id=entry["track_id"],
                    position=entry["position"],
                    added_at=entry.get("added_at"),
                    added_by_spotify_id=entry.get("added_by_spotify_id"),
                )
            )

        await self.session.flush()
    async def list_for_user_with_counts(
        self,
        user_id: uuid.UUID,
    ) -> Sequence[tuple[Playlist, int]]:
        result = await self.session.execute(
            select(
                Playlist,
                func.count(PlaylistTrack.id).label("track_count"),
            )
            .outerjoin(
                PlaylistTrack,
                PlaylistTrack.playlist_id == Playlist.id,
            )
            .where(Playlist.user_id == user_id)
            .group_by(Playlist.id)
        )

        return result.all()

    