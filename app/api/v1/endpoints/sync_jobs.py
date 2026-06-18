import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.sync_executor_service import SyncExecutorService

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.repositories.playlist_repository import PlaylistRepository
from app.repositories.sync_job_repository import SyncJobRepository
from app.schemas.sync_job import SyncJobCreateResponse, SyncJobRead
from app.services.sync_job_service import SyncJobService

router = APIRouter(prefix="/sync-jobs", tags=["sync-jobs"])


def _build_service(db: AsyncSession) -> SyncJobService:
    return SyncJobService(
        sync_job_repo=SyncJobRepository(db),
        playlist_repo=PlaylistRepository(db),
    )


@router.post("", response_model=SyncJobCreateResponse)
async def create_sync_job(
    playlist_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = _build_service(db)

    playlist = await PlaylistRepository(db).get_by_id(playlist_id)
    if playlist is None or playlist.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Playlist not found")

    job = await service.create_sync_job(user=current_user, playlist_id=playlist_id)
    executor = SyncExecutorService(sync_job_repo=SyncJobRepository(db),playlist_repo=PlaylistRepository(db),)
    await executor.execute(job)
    await db.commit()

    return SyncJobCreateResponse(id=job.id, status=job.status)


@router.get("", response_model=list[SyncJobRead])
async def list_sync_jobs(

    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = SyncJobRepository(db)
    return await repo.list_for_user(current_user.id)


@router.get("/{job_id}", response_model=SyncJobRead)
async def get_sync_job(
    job_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = SyncJobRepository(db)
    job = await repo.get_user_job(
    current_user.id,
    job_id,
)

    if job is None:
        raise HTTPException(status_code=404, detail="Sync job not found")

    return job