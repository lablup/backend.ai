from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from ai.backend.logging import is_active as logging_active
from ai.backend.manager.models.alembic import invoked_programmatically

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.

if not logging_active.get():
    assert config.config_file_name is not None
    fileConfig(config.config_file_name)

# Import all model modules to register tables with metadata.
# Using pkgutil for automatic discovery to ensure all tables are included.
# This handles both top-level modules (models/*.py) and subpackages (models/{domain}/).
# Subpackages must export Row classes in their __init__.py.
import importlib
import pkgutil

import ai.backend.manager.models

# Subpackages to skip (not containing Row definitions)
_SKIP_SUBPACKAGES = {"alembic", "hasher", "minilang", "rbac"}

for module_info in pkgutil.iter_modules(ai.backend.manager.models.__path__):
    if module_info.ispkg:
        if module_info.name not in _SKIP_SUBPACKAGES:
            importlib.import_module(f"ai.backend.manager.models.{module_info.name}")
    else:
        importlib.import_module(f"ai.backend.manager.models.{module_info.name}")

from ai.backend.manager.models.base import metadata

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


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    config_section = config.get_section(config.config_ini_section)
    if config_section is None:
        raise RuntimeError("Missing sqlalchemy configuration section")
    connectable = async_engine_from_config(
        config_section,
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
    connectable = config.attributes.get("connection", None)
    if connectable is None:
        asyncio.run(run_async_migrations())
    else:
        do_run_migrations(connectable)


if not invoked_programmatically.get():  # when executed via `alembic` commands
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
