from __future__ import with_statement

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from ai.backend.appproxy.coordinator.models.alembic import invoked_programmatically
from ai.backend.appproxy.coordinator.models.base import metadata_obj as metadata
from ai.backend.logging import is_active as logging_active

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.

if not logging_active.get():
    assert config.config_file_name is not None
    fileConfig(config.config_file_name)

# Import the shared metadata and all models.
# (We need to explicilty import models because model modules
# should be executed to add table definitions to the metadata.)

target_metadata = metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    main_section = config.get_section(config.config_ini_section)
    if main_section is None:
        raise ValueError("The alembic configuration does not have the main [alembic] section.")
    connectable = async_engine_from_config(
        main_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connection = config.attributes.get("connection", None)
    if connection is None:
        asyncio.run(run_async_migrations())
    else:
        do_run_migrations(connection)


if not invoked_programmatically.get():  # when executed via `alembic` commands
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
