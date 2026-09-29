from __future__ import annotations

import asyncio
import importlib.resources
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict

import click

from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.cli.alembic_config import (
    ALEMBIC_CONFIG_HELP,
    db_config_loader,
    load_alembic_config,
    resolve_alembic_config,
)
from ai.backend.manager.models.uuid7 import UUID_GENERATE_V7_DDL

if TYPE_CHECKING:
    from .context import CLIContext

log = StructuredLogger(logging.getLogger(__spec__.name))


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


_alembic_config_option = click.option(
    "-f",
    "--alembic-config",
    default=None,
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    metavar="PATH",
    help=ALEMBIC_CONFIG_HELP,
)


@click.group()
def cli() -> None:
    pass


@cli.command()
@_alembic_config_option
@click.pass_obj
def show(cli_ctx: CLIContext, alembic_config: Path | None) -> None:
    """Show the current schema information."""
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory
    from sqlalchemy.engine import Connection

    from ai.backend.manager.repositories.db.engine import create_async_engine

    def _get_current_rev_sync(connection: Connection) -> str | None:
        context = MigrationContext.configure(connection)
        return context.get_current_revision()

    async def _show() -> None:
        resolved = await resolve_alembic_config(alembic_config, db_config_loader(cli_ctx))
        engine = create_async_engine(resolved.db_url)
        try:
            async with engine.begin() as connection:
                current_rev = await connection.run_sync(_get_current_rev_sync)
        finally:
            await engine.dispose()
        script = ScriptDirectory.from_config(resolved.config)
        heads = script.get_heads()
        head_rev = heads[0] if len(heads) > 0 else None
        print(f"Current database revision: {current_rev}")
        print(f"The head revision of available migrations: {head_rev}")

    asyncio.run(_show())


@cli.command()
@_alembic_config_option
@click.option(
    "--output",
    "-o",
    default="-",
    type=click.Path(dir_okay=False, writable=True),
    help="Output file path (default: stdout)",
)
@click.pass_obj
def dump_history(_cli_ctx: CLIContext, alembic_config: Path | None, output: str) -> None:
    """Dump current alembic history in a serialiazable format."""
    from alembic.script import ScriptDirectory

    from ai.backend.common.json import pretty_json_str
    from ai.backend.manager import __version__

    alembic_cfg = load_alembic_config(alembic_config)
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
        print(pretty_json_str(dump))
    else:
        with Path(output).open(mode="w") as fw:
            fw.write(pretty_json_str(dump))


@cli.command()
@click.argument("previous_version", type=str, metavar="VERSION")
@_alembic_config_option
@click.option(
    "--dry-run",
    default=False,
    is_flag=True,
    help="When specified, this command only informs of revisions unapplied without actually applying it to the database.",
)
@click.pass_obj
def apply_missing_revisions(
    cli_ctx: CLIContext, previous_version: str, alembic_config: Path | None, dry_run: bool
) -> None:
    """
    Compare current alembic revision paths with the given serialized
    alembic revision history and try to execute every missing revisions.
    """
    from alembic.runtime.environment import EnvironmentContext
    from alembic.runtime.migration import MigrationStep
    from alembic.script import Script, ScriptDirectory

    from ai.backend.common.json import load_json

    with importlib.resources.as_file(
        importlib.resources.files("ai.backend.manager.models.alembic.revision_history")
    ) as f:
        try:
            with (f / f"{previous_version}.json").open() as fr:
                revision_history: RevisionHistory = load_json(fr.read())
        except FileNotFoundError:
            log.error(
                "could not find the revision history dump for the previous version; upgrade this cluster to the latest release of the prior major version first",
                previous_version=previous_version,
            )
            sys.exit(1)

    if dry_run:
        alembic_cfg = load_alembic_config(alembic_config)
    else:
        # env.py connects on its own from the config's sqlalchemy.url.
        alembic_cfg = asyncio.run(
            resolve_alembic_config(alembic_config, db_config_loader(cli_ctx))
        ).config
    script_directory = ScriptDirectory.from_config(alembic_cfg)
    revisions_to_apply: dict[str, Script] = {}

    for sc in script_directory.walk_revisions(base="base", head="heads"):
        revisions_to_apply[sc.revision] = sc

    for applied_revision in revision_history["revisions"]:
        del revisions_to_apply[applied_revision["revision"]]

    scripts = list(revisions_to_apply.values())[::-1]
    log.info("applying revisions", revision_count=len(scripts))

    for script_to_apply in scripts:
        log.info("applying revision", revision=str(script_to_apply))

    if not dry_run:
        with EnvironmentContext(
            alembic_cfg,
            script_directory,
            fn=lambda _rev, _con: [
                MigrationStep.upgrade_from_script(script_directory.revision_map, script_to_apply)
                for script_to_apply in scripts
            ],
            destination_rev=script_to_apply.revision,
        ):
            script_directory.run_env()


@cli.command()
@click.argument("revision", default="head", metavar="[REVISION]")
@_alembic_config_option
@click.pass_obj
def upgrade(cli_ctx: CLIContext, revision: str, alembic_config: Path | None) -> None:
    """
    Upgrade the database schema to REVISION (default: head) by applying
    the pending migrations packaged with this manager.
    """
    from alembic import command
    from sqlalchemy.engine import Connection

    from ai.backend.manager.repositories.db.engine import create_async_engine

    async def _upgrade() -> None:
        resolved = await resolve_alembic_config(alembic_config, db_config_loader(cli_ctx))
        alembic_cfg = resolved.config

        def _upgrade_sync(connection: Connection) -> None:
            # env.py runs the migrations on this connection instead of opening its own.
            alembic_cfg.attributes["connection"] = connection
            command.upgrade(alembic_cfg, revision)

        engine = create_async_engine(resolved.db_url)
        try:
            async with engine.begin() as connection:
                await connection.run_sync(_upgrade_sync)
        finally:
            await engine.dispose()
        log.info("upgraded the database schema", revision=revision)

    asyncio.run(_upgrade())


@cli.command()
@_alembic_config_option
@click.pass_obj
def oneshot(cli_ctx: CLIContext, alembic_config: Path | None) -> None:
    """
    Set up your database with one-shot schema migration instead of
    iterating over multiple revisions if there is no existing database.
    The database connection comes from the alembic config's sqlalchemy.url,
    or from the [db] section of manager.toml when it has none.

    Reference: http://alembic.sqlalchemy.org/en/latest/cookbook.html
               #building-an-up-to-date-database-from-scratch
    """
    from alembic.config import Config
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory
    from sqlalchemy.engine import Connection, Engine

    from ai.backend.manager.models.base import ensure_all_tables_registered, metadata
    from ai.backend.manager.models.global_entity.seed import SEED_GLOBAL_ENTITIES_SQL
    from ai.backend.manager.repositories.db.engine import create_async_engine

    ensure_all_tables_registered()

    def _get_current_rev_sync(connection: Connection) -> str | None:
        context = MigrationContext.configure(connection)
        return context.get_current_revision()

    def _create_all_sync(connection: Connection, engine: Engine, alembic_cfg: Config) -> None:
        alembic_cfg.attributes["connection"] = connection
        metadata.create_all(engine, checkfirst=False)
        for statement in SEED_GLOBAL_ENTITIES_SQL:
            connection.exec_driver_sql(statement)
        log.info("stamping the alembic version to head")
        script = ScriptDirectory.from_config(alembic_cfg)
        heads = script.get_heads()
        if not heads:
            log.warning("no alembic migration heads found, skipping version stamping")
            return
        head_rev = heads[0]
        connection.exec_driver_sql("CREATE TABLE alembic_version (\nversion_num varchar(32)\n);")
        connection.exec_driver_sql(f"INSERT INTO alembic_version VALUES('{head_rev}')")

    async def _oneshot() -> None:
        resolved = await resolve_alembic_config(alembic_config, db_config_loader(cli_ctx))
        engine = create_async_engine(resolved.db_url)
        try:
            async with engine.begin() as connection:
                await connection.exec_driver_sql('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
                await connection.exec_driver_sql(UUID_GENERATE_V7_DDL)
                current_rev = await connection.run_sync(_get_current_rev_sync)
            if current_rev is None:
                # For a fresh clean database, create all from scratch.
                # (it will raise error if tables already exist.)
                log.info("detected a fresh new database, creating tables")
                async with engine.begin() as connection:
                    await connection.run_sync(
                        _create_all_sync,
                        engine=engine.sync_engine,
                        alembic_cfg=resolved.config,
                    )
                log.info(
                    "if old migrations are not needed, delete them and set down_revision "
                    "of the earliest migration to None"
                )
            else:
                log.info(
                    "detected an existing database; use 'backend.ai mgr schema upgrade' to apply pending migrations",
                    current_revision=current_rev,
                )
        finally:
            await engine.dispose()

    asyncio.run(_oneshot())
