"""Alembic environment configuration.

This script sets up the context in which Alembic will run migrations.
It loads the SQLAlchemy metadata from the application's models and
configures the connection to the database. When an environment variable
`DATABASE_URL` is present, it will take precedence over the
`sqlalchemy.url` defined in the `alembic.ini` file. This allows
development and production environments to provide their own connection
strings without editing configuration files.
"""

from __future__ import annotations

import os
from logging.config import fileConfig
from pathlib import Path
import sys
from dotenv import load_dotenv

from sqlalchemy import engine_from_config, pool
from alembic import context

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # db/migrations/env.py -> db/migrations -> db -> PROJECT
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from core.domain.models import Base  # noqa: F401 - imported for metadata

# this is the Alembic Config object, which provides access to the values
# within the .ini file in use.
config = context.config

# Interpret the config file for Python logging. This line sets up loggers
fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def get_database_url() -> str:
    """Retrieve the database URL from environment or config.

    Returns the `DATABASE_URL` environment variable if it exists,
    otherwise falls back to the `sqlalchemy.url` entry in the Alembic
    configuration file.
    """
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    return config.get_main_option("sqlalchemy.url")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine. By
    skipping the Engine creation we don't even need a DBAPI to be
    available. Calls to context.execute() here emit the given string to
    the script output.
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a
    connection with the context.
    """
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()