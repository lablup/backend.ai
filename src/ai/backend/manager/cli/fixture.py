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
from ai.backend.logging.structured import StructuredLogger
from ai.backend.manager.models.base import populate_fixture
from ai.backend.manager.repositories.db.engine import build_db_url

if TYPE_CHECKING:
    from .context import CLIContext

log = StructuredLogger(logging.getLogger(__spec__.name))


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.argument("fixture_path", type=Path)
@click.pass_obj
def populate(cli_ctx: CLIContext, fixture_path: Path) -> None:
    async def _impl() -> None:
        log.info("populating the fixture", fixture_path=fixture_path)
        try:
            fixture = load_json(fixture_path.read_text(encoding="utf8"))
        except AttributeError:
            log.error("no such fixture", fixture_path=fixture_path)
            return
        bootstrap_config = await cli_ctx.get_bootstrap_config()
        engine = create_async_engine(build_db_url(bootstrap_config.db))
        try:
            await populate_fixture(engine, fixture)
        except Exception:
            log.exception("failed to populate fixtures", fixture_path=fixture_path)
            sys.exit(ExitCode.FAILURE)
        else:
            log.info("populated the fixture; rows that already existed may have been skipped")
        finally:
            await engine.dispose()

    """Populate fixtures."""
    asyncio.run(_impl())


@cli.command()
@click.pass_obj
def list(_cli_ctx: CLIContext) -> None:
    """List all available fixtures."""
    log.warning("this command is deprecated")
