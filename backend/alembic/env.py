import os
import re
import sys
from logging.config import fileConfig
from pathlib import Path
import sqlalchemy as sa
from sqlalchemy import pool, create_engine
from alembic import context

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.database.database import Base
from app.database import models  # Ensures all models are registered

config = context.config


def get_target_url() -> str:
    """
    Resolves the migration target database URL with strict precedence:
    1. os.environ['DATABASE_URL'] (highest priority)
    2. config.get_main_option('sqlalchemy.url') (if valid and not driver:// placeholder)
    3. settings.DATABASE_URL (defaults to local SQLite)
    """
    env_url = os.getenv("DATABASE_URL", "").strip()
    if env_url:
        url = env_url
    else:
        cfg_url = config.get_main_option("sqlalchemy.url")
        if cfg_url and not cfg_url.startswith("driver://"):
            url = cfg_url
        else:
            url = settings.DATABASE_URL

    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


target_url = get_target_url()

# Safe escaping for ConfigParser:
# ConfigParser interprets '%' as interpolation syntax (e.g. %(here)s).
# If passwords contain URL-encoded chars (%40, %25, etc.), set_main_option will fail
# with ValueError: invalid interpolation syntax unless '%' is escaped to '%%'.
# re.sub(r'%(?!%)', '%%', ...) safely escapes single '%' to '%%' idempotently.
if target_url:
    safe_config_url = re.sub(r'%(?!%)', '%%', target_url)
    config.set_main_option("sqlalchemy.url", safe_config_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# render_as_batch is required only for SQLite (which cannot natively ALTER TABLE columns).
# On PostgreSQL this is disabled to generate native ALTER TABLE statements.
_use_batch = "sqlite" in target_url.lower()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    Configures the context with the target URL directly (immune to ConfigParser).
    Calls to context.execute() emit the DDL to the script output.
    """
    url = get_target_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=_use_batch,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    Prefers an existing active connection passed via config.attributes['connection'].
    Otherwise creates an Engine directly from target_url (completely avoiding
    ConfigParser interpolation bugs).
    """
    connectable = config.attributes.get("connection", None)

    if connectable is not None:
        if isinstance(connectable, sa.engine.Connection):
            context.configure(
                connection=connectable,
                target_metadata=target_metadata,
                render_as_batch=_use_batch,
            )
            with context.begin_transaction():
                context.run_migrations()
        else:
            with connectable.connect() as connection:
                context.configure(
                    connection=connection,
                    target_metadata=target_metadata,
                    render_as_batch=_use_batch,
                )
                with context.begin_transaction():
                    context.run_migrations()
    else:
        url = get_target_url()
        connectable = create_engine(
            url,
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                render_as_batch=_use_batch,
            )
            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
