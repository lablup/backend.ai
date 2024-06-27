from __future__ import annotations

import asyncio
import importlib.resources
import json
import logging
import sys
from typing import TYPE_CHECKING, TypedDict

import click
from alembic import command
from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.runtime.migration import MigrationContext, MigrationStep
from alembic.script import Script, ScriptDirectory
from sqlalchemy.engine import Connection, Engine

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.manager import __version__

from ..models.alembic import invoked_programmatically
from ..models.base import metadata
from ..models.utils import create_async_engine

if TYPE_CHECKING:
    from .context import CLIContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


class RevisionDump(TypedDict):
    down_revision: str | None
    revision: str
    is_head: bool
    is_branch_point: bool
    is_merge_point: bool
    doc: str


class RevisionHistory(TypedDict):
    manager_version: str
    revisions: list[RevisionDump]


@click.group()
def cli(args) -> None:
    pass


@cli.command()
@click.option(
    "-f",
    "--alembic-config",
    default="alembic.ini",
    metavar="PATH",
    help="The path to Alembic config file. [default: alembic.ini]",
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
    type=click.Path(exists=True, dir_okay=False),
    metavar="PATH",
    help="The path to Alembic config file. [default: alembic.ini]",
)
@click.option(
    "--output",
    "-o",
    default="-",
    type=click.Path(dir_okay=False, writable=True),
    help="Output file path (default: stdout)",
)
@click.pass_obj
def dump_history(cli_ctx: CLIContext, alembic_config: str, output: str) -> None:
    """Dump current alembic history in a serialiazable format."""

    alembic_cfg = Config(alembic_config)
    script = ScriptDirectory.from_config(alembic_cfg)
    serialized_revisions = []

    for sc in script.walk_revisions(base="base", head="heads"):
        revision_dump = RevisionDump(
            down_revision=sc._format_down_revision() if sc.down_revision else None,
            revision=sc.revision,
            is_head=sc.is_head,
            is_branch_point=sc.is_branch_point,
            is_merge_point=sc.is_merge_point,
            doc=sc.doc,
        )
        serialized_revisions.append(revision_dump)

    dump = RevisionHistory(manager_version=__version__, revisions=serialized_revisions)

    if output == "-" or output is None:
        print(json.dumps(dump, ensure_ascii=False, indent=2))
    else:
        with open(output, mode="w") as fw:
            fw.write(json.dumps(dump, ensure_ascii=False, indent=2))


@cli.command()
@click.argument("previous_version", type=str, metavar="VERSION")
@click.option(
    "-f",
    "--alembic-config",
    default="alembic.ini",
    type=click.Path(exists=True, dir_okay=False),
    metavar="PATH",
    help="The path to Alembic config file. [default: alembic.ini]",
)
@click.option(
    "--dry-run",
    default=False,
    is_flag=True,
    help="When specified, this command only informs of revisions unapplied without actually applying it to the database.",
)
@click.pass_obj
def apply_missing_revisions(
    cli_ctx: CLIContext, previous_version: str, alembic_config: str, dry_run: bool
) -> None:
    """
    Compare current alembic revision paths with the given serialized
    alembic revision history and try to execute every missing revisions.
    """
    with importlib.resources.as_file(
        importlib.resources.files("ai.backend.manager.models.alembic.revision_history")
    ) as f:
        try:
            with open(f / f"{previous_version}.json", "r") as fr:
                revision_history: RevisionHistory = json.loads(fr.read())
        except FileNotFoundError:
            log.error(
                "Could not find revision history dump as of Backend.AI version {}. Make sure you have upgraded this Backend.AI cluster to very latest version of prior major release before initiating this major upgrade.",
                previous_version,
            )
            sys.exit(1)

    alembic_cfg = Config(alembic_config)
    script_directory = ScriptDirectory.from_config(alembic_cfg)
    revisions_to_apply: dict[str, Script] = {}

    for sc in script_directory.walk_revisions(base="base", head="heads"):
        revisions_to_apply[sc.revision] = sc

    for applied_revision in revision_history["revisions"]:
        del revisions_to_apply[applied_revision["revision"]]

    log.info("Applying following revisions:")
    scripts = list(revisions_to_apply.values())[::-1]

    for script_to_apply in scripts:
        log.info("    {}", str(script_to_apply))

    if not dry_run:
        with EnvironmentContext(
            alembic_cfg,
            script_directory,
            fn=lambda rev, con: [
                MigrationStep.upgrade_from_script(script_directory.revision_map, script_to_apply)
                for script_to_apply in scripts
            ],
            destination_rev=script_to_apply.revision,
        ):
            script_directory.run_env()


@cli.command()
@click.option(
    "-f",
    "--alembic-config",
    default="alembic.ini",
    type=click.Path(exists=True, dir_okay=False),
    metavar="PATH",
    help="The path to Alembic config file. [default: alembic.ini]",
)
@click.pass_obj
def oneshot(cli_ctx: CLIContext, alembic_config: str) -> None:
    """
    Set up your database with one-shot schema migration instead of
    iterating over multiple revisions if there is no existing database.
    It uses alembic.ini to configure database connection.

    Reference: http://alembic.sqlalchemy.org/en/latest/cookbook.html
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

    alembic_cfg = Config(alembic_config)
    sa_url = alembic_cfg.get_main_option("sqlalchemy.url")
    assert sa_url is not None
    sa_url = sa_url.replace("postgresql://", "postgresql+asyncpg://")
    asyncio.run(_oneshot(sa_url))
