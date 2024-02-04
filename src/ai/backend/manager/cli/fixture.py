from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import quote_plus as urlquote

import click
import sqlalchemy as sa

from ai.backend.common.logging import BraceStyleAdapter

from ..models.base import populate_fixture

if TYPE_CHECKING:
    from .context import CLIContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


@click.group()
def cli():
    pass


@cli.command()
@click.argument("fixture_path", type=Path)
@click.pass_obj
def populate(cli_ctx: CLIContext, fixture_path: Path) -> None:
    async def _impl():
        log.info("Populating fixture '{0}' ...", fixture_path)
        try:
            fixture = json.loads(fixture_path.read_text(encoding="utf8"))
        except AttributeError:
            log.error("No such fixture.")
            return
        db_username = cli_ctx.local_config["db"]["user"]
        db_password = cli_ctx.local_config["db"]["password"]
        db_addr = cli_ctx.local_config["db"]["addr"]
        db_name = cli_ctx.local_config["db"]["name"]
        engine = sa.ext.asyncio.create_async_engine(
            f"postgresql+asyncpg://{urlquote(db_username)}:{urlquote(db_password)}@{db_addr}/{db_name}",
        )
        try:
            await populate_fixture(engine, fixture)
        except Exception:
            log.exception(
                "Failed to populate fixtures from {} due to the following error:", fixture_path
            )
        else:
            log.info("Done")
            log.warning("Some rows may be skipped if they already exist.")
        finally:
            await engine.dispose()

    """Populate fixtures."""
    asyncio.run(_impl())


@cli.command()
@click.pass_obj
def list(cli_ctx: CLIContext) -> None:
    """List all available fixtures."""
    log.warning("This command is deprecated.")
