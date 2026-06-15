from app.models.user import User
from app.repositories.playlist_repository import PlaylistRepository
from app.repositories.track_repository import TrackRepository
from app.repositories.playlist_track_repository import PlaylistTrackRepository
from app.schemas.playlist import PlaylistImportResponse
from app.services.spotify import SpotifyService
from datetime import datetime


class PlaylistImportService:
    def __init__(
        self,
        playlist_repo: PlaylistRepository,
        track_repo: TrackRepository,
        playlist_track_repo: PlaylistTrackRepository,
        spotify_service: SpotifyService,
    ):
        self.playlist_repo = playlist_repo
        self.track_repo = track_repo
        self.playlist_track_repo = playlist_track_repo
        self.spotify_service = spotify_service

    async def import_playlist(
        self,
        current_user: User,
        spotify_playlist_id: str,
    ) -> PlaylistImportResponse:
        playlist_data = await self.spotify_service.get_playlist(
            current_user, spotify_playlist_id
        )
        existing = await self.playlist_repo.get_by_user_spotify_id(
        current_user.id,
        playlist_data["id"],
        )
        if (existing is not None and existing.snapshot_id == playlist_data.get("snapshot_id")):


            return PlaylistImportResponse(
            playlist_id=existing.id,
            playlist_name=existing.name,
            tracks_imported=0,
        )
    
        playlist = await self.playlist_repo.upsert(
            user_id=current_user.id,
            spotify_playlist_id=playlist_data["id"],
            name=playlist_data["name"],
            description=playlist_data.get("description"),
            snapshot_id=playlist_data.get("snapshot_id"),
        )
        
        items = playlist_data["items"]["items"]

        tracks_data = []
        item_meta = []

        for item in items:
            track_info = item.get("item")
            if track_info is None or track_info.get("id") is None:
                continue

            artist_names = ", ".join(
                artist["name"] for artist in track_info.get("artists", [])
            )

            album = track_info.get("album", {})

            tracks_data.append(
            {
                "spotify_id": track_info["id"],
                "name": track_info["name"],
                "artist_names": artist_names,
                "album_name": album.get("name"),
                "album_image_url": (
                    album.get("images", [{}])[0].get("url")
                    if album.get("images")
                    else None
                ),
                "duration_ms": track_info.get("duration_ms"),
                "isrc": track_info.get("external_ids", {}).get("isrc"),
                "is_explicit": track_info.get("explicit", False),
                "preview_url": track_info.get("preview_url"),
            }
        )

            item_meta.append(
                {
                "added_at": datetime.fromisoformat(
            item["added_at"].replace("Z", "+00:00")
        ).replace(tzinfo=None)
        if item.get("added_at") else None,
        "added_by_spotify_id": (item.get("added_by") or {}).get("id"),
                }
            )

        #print("TRACKS_DATA_COUNT:", len(tracks_data))

        upserted_tracks = await self.track_repo.bulk_upsert(tracks_data)

        #print("UPSERTED_COUNT:", len(upserted_tracks))

        ordered_tracks = []
        for position, (track, meta) in enumerate(zip(upserted_tracks, item_meta)):
            ordered_tracks.append(
                {
                    "track_id": track.id,
                    "position": position,
                    "added_at": meta["added_at"],
                    "added_by_spotify_id": meta["added_by_spotify_id"],
                }
            )

        await self.playlist_repo.replace_tracks(playlist.id, ordered_tracks)

        return PlaylistImportResponse(
            playlist_id=playlist.id,
            playlist_name=playlist.name,
            tracks_imported=len(ordered_tracks),
        )