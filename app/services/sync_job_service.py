import uuid

from app.models.sync_job import SyncJob
from app.models.user import User
from app.repositories.playlist_repository import PlaylistRepository
from app.repositories.sync_job_repository import SyncJobRepository

class SyncJobService:
    def __init__(
self,
sync_job_repo: SyncJobRepository,
playlist_repo: PlaylistRepository,
) -> None:
        self.sync_job_repo = sync_job_repo
        self.playlist_repo = playlist_repo


    async def create_sync_job(
    self,
    user: User,
    playlist_id: uuid.UUID,
) -> SyncJob:
        return await self.sync_job_repo.create(
        user_id=user.id,
        playlist_id=playlist_id,
    )

