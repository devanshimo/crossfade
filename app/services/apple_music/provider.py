from abc import ABC, abstractmethod

from app.schemas.apple_music import AppleTrackMatch


class AppleMusicProvider(ABC):

    @abstractmethod
    async def search_track(
        self,
        name: str,
        artist_names: str,
        isrc: str | None,
    ) -> AppleTrackMatch | None: ...