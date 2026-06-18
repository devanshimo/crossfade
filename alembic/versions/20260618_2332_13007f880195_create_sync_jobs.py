"""create_sync_jobs

Revision ID: 13007f880195
Revises: 8b4385dfe916
Create Date: 2026-06-18 23:32:04.877719

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "13007f880195"
down_revision = "8b4385dfe916"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sync_jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "playlist_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("playlists.id"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "running",
                "completed",
                "failed",
                name="syncjobstatus",
            ),
            nullable=False,
        ),
        sa.Column(
            "total_tracks",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "matched_tracks",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "synced_tracks",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "started_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_sync_jobs_user_id",
        "sync_jobs",
        ["user_id"],
    )

    op.create_index(
        "ix_sync_jobs_playlist_id",
        "sync_jobs",
        ["playlist_id"],
    )

    op.create_index(
        "ix_sync_jobs_status",
        "sync_jobs",
        ["status"],
    )

    op.create_index(
        "ix_sync_jobs_created_at",
        "sync_jobs",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_sync_jobs_created_at",
        table_name="sync_jobs",
    )

    op.drop_index(
        "ix_sync_jobs_status",
        table_name="sync_jobs",
    )

    op.drop_index(
        "ix_sync_jobs_playlist_id",
        table_name="sync_jobs",
    )

    op.drop_index(
        "ix_sync_jobs_user_id",
        table_name="sync_jobs",
    )

    op.drop_table("sync_jobs")

    op.execute(
        "DROP TYPE IF EXISTS syncjobstatus"
    )