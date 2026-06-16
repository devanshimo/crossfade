"""add apple music fields to tracks

Revision ID: 8b4385dfe916
Revises: bd9402f3205a
Create Date: 2026-06-16 16:22:00.078311

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = '8b4385dfe916'
down_revision: str | None = 'bd9402f3205a'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "tracks",
        sa.Column("isrc", sa.String(), nullable=True),
    )

    op.add_column(
        "tracks",
        sa.Column("apple_music_id", sa.String(), nullable=True),
    )

    op.create_index(
        "ix_tracks_isrc",
        "tracks",
        ["isrc"],
    )

    op.create_index(
        "ix_tracks_apple_music_id",
        "tracks",
        ["apple_music_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_tracks_apple_music_id",
        table_name="tracks",
    )

    op.drop_index(
        "ix_tracks_isrc",
        table_name="tracks",
    )

    op.drop_column(
        "tracks",
        "apple_music_id",
    )

    op.drop_column(
        "tracks",
        "isrc",
    )
