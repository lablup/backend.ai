from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import click
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.engine import Connection, Engine

from ai.backend.common.logging import BraceStyleAdapter

from ..models.alembic import invoked_programmatically
from ..models.base import metadata
from ..models.utils import create_async_engine

if TYPE_CHECKING:
    from .context import CLIContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


@click.group()
def cli(args) -> None:
    pass


@cli.command()
@click.option(
    "-f",
    "--alembic-config",
    default="alembic.ini",
    metavar="PATH",
    help="The path to Alembic config file. " "[default: alembic.ini]",
)
@click.pass_obj
def show(cli_ctx: CLIContext, alembic_config) -> None:
    """Show the current schema information."""

    def _get_current_rev_sync(connection: Connection) -> str | None:
        context = MigrationContext.configure(connection)
        return context.get_current_revision()

    async def _show(sa_url: str) -> None:
        invoked_programmatically.set(True)
        engine = create_async_engine(sa_url)
        async with engine.begin() as connection:
            current_rev = await connection.run_sync(_get_current_rev_sync)
        script = ScriptDirectory.from_config(alembic_cfg)
        heads = script.get_heads()
        head_rev = heads[0] if len(heads) > 0 else None
        print(f"Current database revision: {current_rev}")
        print(f"The head revision of available migrations: {head_rev}")

    with cli_ctx.logger:
        alembic_cfg = Config(alembic_config)
        sa_url = alembic_cfg.get_main_option("sqlalchemy.url")
        assert sa_url is not None
        sa_url = sa_url.replace("postgresql://", "postgresql+asyncpg://")
        asyncio.run(_show(sa_url))


@cli.command()
@click.option(
    "-f",
    "--alembic-config",
    default="alembic.ini",
    metavar="PATH",
    help="The path to Alembic config file. " "[default: alembic.ini]",
)
@click.pass_obj
def oneshot(cli_ctx: CLIContext, alembic_config) -> None:
    """
    Set up your database with one-shot schema migration instead of
    iterating over multiple revisions if there is no existing database.
    It uses alembic.ini to configure database connection.

    Reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
               #building-an-up-to-date-database-from-scratch
    """

    def _get_current_rev_sync(connection: Connection) -> str | None:
        context = MigrationContext.configure(connection)
        return context.get_current_revision()

    def _create_all_sync(connection: Connection, engine: Engine) -> None:
        alembic_cfg.attributes["connection"] = connection
        metadata.create_all(engine, checkfirst=False)
        log.info("Stamping alembic version to head...")
        script = ScriptDirectory.from_config(alembic_cfg)
        head_rev = script.get_heads()[0]
        connection.exec_driver_sql("CREATE TABLE alembic_version (\nversion_num varchar(32)\n);")
        connection.exec_driver_sql(f"INSERT INTO alembic_version VALUES('{head_rev}')")

    def _upgrade_sync(connection: Connection) -> None:
        alembic_cfg.attributes["connection"] = connection
        command.upgrade(alembic_cfg, "head")

    async def _oneshot(sa_url: str) -> None:
        invoked_programmatically.set(True)
        engine = create_async_engine(sa_url)
        async with engine.begin() as connection:
            await connection.exec_driver_sql('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
            current_rev = await connection.run_sync(_get_current_rev_sync)
        if current_rev is None:
            # For a fresh clean database, create all from scratch.
            # (it will raise error if tables already exist.)
            log.info("Detected a fresh new database.")
            log.info("Creating tables...")
            async with engine.begin() as connection:
                await connection.run_sync(_create_all_sync, engine=engine.sync_engine)
        else:
            # If alembic version info is already available, perform incremental upgrade.
            log.info("Detected an existing database.")
            log.info("Performing schema upgrade to head...")
            async with engine.begin() as connection:
                await connection.run_sync(_upgrade_sync)

        log.info(
            "If you don't need old migrations, delete them and set "
            '"down_revision" value in the earliest migration to "None".'
        )

    with cli_ctx.logger:
        alembic_cfg = Config(alembic_config)
        sa_url = alembic_cfg.get_main_option("sqlalchemy.url")
        assert sa_url is not None
        sa_url = sa_url.replace("postgresql://", "postgresql+asyncpg://")
        asyncio.run(_oneshot(sa_url))
