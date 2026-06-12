"""
alembic/env.py
───────────────
Alembic migration environment – the bridge between our ORM models and the
migration engine.

Why it exists:
    Alembic requires this file to (a) know which metadata to inspect for
    autogenerate and (b) know how to connect to the database.

Key design decisions:
    • We import ALL models here (via the `app.models` package) so Alembic's
      autogenerate can see every table.  If a new model file is created, add
      its import to app/models/__init__.py and it will be picked up.
    • DATABASE_URL comes from Pydantic Settings (not alembic.ini) so `.env`
      is the single source of truth.
    • Alembic doesn't support asyncpg natively, so we swap `+asyncpg` for
      `+psycopg2` (sync driver) for migration runs only.  The running app
      continues to use asyncpg.
"""

import re
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# ── Make sure `app` is importable from alembic/ ──────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# ── Import Base + all models so metadata is populated ────────────────────────
from app.db.base import Base  # noqa: E402
import app.models  # noqa: E402, F401  – registers all ORM models with Base.metadata

# ── Pydantic Settings for DATABASE_URL ───────────────────────────────────────
from app.core.config import get_settings  # noqa: E402

settings = get_settings()

# ── Alembic Config object ─────────────────────────────────────────────────────
config = context.config

# Apply logging config from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Swap asyncpg → psycopg2 so Alembic can use a synchronous connection
sync_url = re.sub(r"\+asyncpg", "+psycopg2", settings.database_url)
config.set_main_option("sqlalchemy.url", sync_url)

target_metadata = Base.metadata


# ── Offline mode (generates SQL without a live DB) ───────────────────────────

def run_migrations_offline() -> None:
    """
    Emit migration SQL to stdout without connecting to the database.

    Useful for review, CI, or DBAs who apply scripts manually.
    Run with: `alembic upgrade head --sql`
    """
    context.configure(
        url=sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online mode (runs against a live DB) ─────────────────────────────────────

def run_migrations_online() -> None:
    """
    Connect to the database and run migrations in a transaction.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,    # disposable connection for migration runs
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,      # detect column type changes
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
