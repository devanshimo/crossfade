from app.models.sync_job import SyncJob
from app.repositories.sync_job_repository import SyncJobRepository
from app.repositories.playlist_repository import PlaylistRepository

class SyncExecutorService:
    def __init__(
self,
sync_job_repo: SyncJobRepository,
playlist_repo: PlaylistRepository,
) -> None:
        self.sync_job_repo = sync_job_repo
        self.playlist_repo = playlist_repo


    async def execute(
        self,
        job: SyncJob,
    ) -> SyncJob:
        await self.sync_job_repo.mark_running(job)

        try:
            playlist = await self.playlist_repo.get_with_tracks(
                job.playlist_id
            )

            if playlist:
                job.total_tracks = len(
                    playlist.playlist_tracks
                )

            return await self.sync_job_repo.mark_completed(job)

        except Exception as exc:
            return await self.sync_job_repo.mark_failed(
                job,
                str(exc),
            )