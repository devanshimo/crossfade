from app.schemas.apple_music import AppleTrackMatch
from app.services.apple_music.provider import AppleMusicProvider


class MockAppleMusicProvider(AppleMusicProvider):
    async def search_track(
        self,
        name: str,
        artist_names: str,
        isrc: str | None,
    ) -> AppleTrackMatch | None:
        return None