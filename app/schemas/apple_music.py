from pydantic import BaseModel


class AppleTrackMatch(BaseModel):
    apple_music_id: str
    name: str
    artist_name: str