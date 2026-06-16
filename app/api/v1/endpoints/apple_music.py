from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User

from app.repositories.track_repository import TrackRepository

from app.services.apple_music.mock_provider import (
    MockAppleMusicProvider,
)
from app.services.apple_track_match_service import (
    AppleTrackMatchService,
)

router = APIRouter(
    prefix="/apple-music",
    tags=["apple-music"],
)


@router.post("/match")
async def match_tracks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    track_repo = TrackRepository(db)

    provider = MockAppleMusicProvider()

    service = AppleTrackMatchService(
        track_repository=track_repo,
        apple_provider=provider,
    )

    matched = await service.match_unmatched_tracks()

    await db.commit()

    return {
        "matched": matched,
    }