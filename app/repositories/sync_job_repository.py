import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sync_job import SyncJob, SyncJobStatus


class SyncJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user_id: uuid.UUID, playlist_id: uuid.UUID) -> SyncJob:
        job = SyncJob(user_id=user_id, playlist_id=playlist_id, status=SyncJobStatus.pending)
        self.session.add(job)
        await self.session.flush()
        return job

    async def get_by_id(self, job_id: uuid.UUID) -> Optional[SyncJob]:
        result = await self.session.execute(select(SyncJob).where(SyncJob.id == job_id))
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: uuid.UUID) -> list[SyncJob]:
        result = await self.session.execute(
            select(SyncJob).where(SyncJob.user_id == user_id).order_by(SyncJob.created_at.desc())
        )
        return list(result.scalars().all())

    async def mark_running(self, job: SyncJob) -> SyncJob:
        job.status = SyncJobStatus.running
        job.started_at = datetime.utcnow()
        await self.session.flush()
        return job

    async def mark_completed(self, job: SyncJob) -> SyncJob:
        job.status = SyncJobStatus.completed
        job.completed_at = datetime.utcnow()
        await self.session.flush()
        return job

    async def mark_failed(self, job: SyncJob, error_message: str) -> SyncJob:
        job.status = SyncJobStatus.failed
        job.completed_at = datetime.utcnow()
        job.error_message = error_message
        await self.session.flush()
        return job
    async def get_user_job(
    self,
    user_id: uuid.UUID,
    job_id: uuid.UUID,
) -> Optional[SyncJob]:
        result = await self.session.execute(
        select(SyncJob).where(
            SyncJob.id == job_id,
            SyncJob.user_id == user_id,
        )
    )
        return result.scalar_one_or_none()