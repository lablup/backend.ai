from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import click
from sqlalchemy.ext.asyncio import create_async_engine

from ai.backend.cli.types import ExitCode
from ai.backend.common.json import load_json
from ai.backend.logging import BraceStyleAdapter
from ai.backend.manager.models.base import populate_fixture

if TYPE_CHECKING:
    from .context import CLIContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.argument("fixture_path", type=Path)
@click.pass_obj
def populate(cli_ctx: CLIContext, fixture_path: Path) -> None:
    async def _impl() -> None:
        log.info("Populating fixture '{0}' ...", fixture_path)
        try:
            fixture = load_json(fixture_path.read_text(encoding="utf8"))
        except AttributeError:
            log.error("No such fixture.")
            return
        bootstrap_config = await cli_ctx.get_bootstrap_config()
        engine = create_async_engine(bootstrap_config.db.sqlalchemy_url())
        try:
            await populate_fixture(engine, fixture)
        except Exception:
            log.exception(
                "Failed to populate fixtures from {} due to the following error:", fixture_path
            )
            sys.exit(ExitCode.FAILURE)
        else:
            log.info("Done")
            log.warning("Some rows may be skipped if they already exist.")
        finally:
            await engine.dispose()

    """Populate fixtures."""
    asyncio.run(_impl())


@cli.command()
@click.pass_obj
def list(_cli_ctx: CLIContext) -> None:
    """List all available fixtures."""
    log.warning("This command is deprecated.")
