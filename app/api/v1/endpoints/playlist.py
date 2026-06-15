from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.playlist import PlaylistImportRequest, PlaylistImportResponse, PlaylistListItem, PlaylistRead
from app.repositories.playlist_repository import PlaylistRepository
from app.repositories.track_repository import TrackRepository
from app.repositories.playlist_track_repository import PlaylistTrackRepository
from app.services.playlist_import import PlaylistImportService
from app.services.spotify import SpotifyService

router = APIRouter(prefix="/playlists", tags=["playlists"])


@router.post("/import", response_model=PlaylistImportResponse)
async def import_playlist(
    payload: PlaylistImportRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    playlist_repo = PlaylistRepository(db)
    track_repo = TrackRepository(db)
    playlist_track_repo = PlaylistTrackRepository(db)
    spotify_service = SpotifyService(db)

    service = PlaylistImportService(
        playlist_repo=playlist_repo,
        track_repo=track_repo,
        playlist_track_repo=playlist_track_repo,
        spotify_service=spotify_service,
    )

    result = await service.import_playlist(
        current_user=current_user,
        spotify_playlist_id=payload.spotify_playlist_id,
    )
    await db.commit()
    return result
@router.get("/test-playlists")
async def test_playlists(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SpotifyService(db)

    playlists = await service.get_current_user_playlists(current_user)

    return {
        "count": len(playlists),
        "first_playlist": playlists[0] if playlists else None,
    }
@router.get("/test-playlist-tracks/{playlist_id}")
async def test_playlist_tracks(
    playlist_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SpotifyService(db)

    playlist = await service.get_playlist(
    current_user,
    playlist_id,
)

    return {
    "playlist": playlist
}
@router.get("", response_model=list[PlaylistListItem])
async def list_playlists(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    playlist_repo = PlaylistRepository(db)
    rows = await playlist_repo.list_for_user_with_counts(current_user.id)

    return [
        PlaylistListItem(
            id=playlist.id,
            spotify_playlist_id=playlist.spotify_playlist_id,
            name=playlist.name,
            description=playlist.description,
            snapshot_id=playlist.snapshot_id,
            created_at=playlist.created_at,
            updated_at=playlist.updated_at,
            track_count=track_count,
        )
        for playlist, track_count in rows
    ]


@router.get("/{playlist_id}", response_model=PlaylistRead)
async def get_playlist_detail(
    playlist_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    playlist_repo = PlaylistRepository(db)
    playlist = await playlist_repo.get_with_tracks(playlist_id)

    if playlist is None or playlist.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Playlist not found")

    return PlaylistRead(
        id=playlist.id,
        spotify_playlist_id=playlist.spotify_playlist_id,
        name=playlist.name,
        description=playlist.description,
        snapshot_id=playlist.snapshot_id,
        created_at=playlist.created_at,
        updated_at=playlist.updated_at,
        tracks=[pt.track for pt in playlist.playlist_tracks],
    )

   