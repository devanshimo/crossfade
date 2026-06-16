from app.models.track import Track
from app.repositories.track_repository import TrackRepository
from app.services.apple_music.provider import AppleMusicProvider


class AppleTrackMatchService:
    def __init__(
        self,
        track_repository: TrackRepository,
        apple_provider: AppleMusicProvider,
    ) -> None:
        self.track_repository = track_repository
        self.apple_provider = apple_provider

    async def match_track(self, track: Track) -> bool:
        if track.apple_music_id:
            return False

        match = await self.apple_provider.search_track(
            name=track.name,
            artist_names=track.artist_names,
            isrc=track.isrc,
        )

        if match is None:
            return False

        track.apple_music_id = match.apple_music_id
        return True

    async def match_unmatched_tracks(self) -> int:
        tracks = await self.track_repository.get_unmatched_tracks()
        count = 0
        for track in tracks:
            matched = await self.match_track(track)
            if matched:
                count += 1
        await self.track_repository.session.flush()
        return count