from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import click

from ai.backend.common import redis_helper
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.manager.cli.context import redis_ctx

if TYPE_CHECKING:
    from .context import CLIContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.pass_obj
def ping(cli_ctx: CLIContext) -> None:
    """
    Check whether redis database is healthy or not.
    """

    async def _impl():
        async with redis_ctx(cli_ctx) as redis_conn_set:
            try:
                await redis_helper.execute(
                    redis_conn_set.live,
                    lambda r: r.execute_command("PING"),
                )
                log.info("REDIS_LIVE_DB is ok")
            except Exception:
                log.exception("REDIS_LIVE_DB is not ok")
            try:
                await redis_helper.execute(
                    redis_conn_set.stat,
                    lambda r: r.execute_command("PING"),
                )
                log.info("REDIS_STAT_DB is ok")
            except Exception:
                log.exception("REDIS_STAT_DB is not ok")
            try:
                await redis_helper.execute(
                    redis_conn_set.image,
                    lambda r: r.execute_command("PING"),
                )
                log.info("REDIS_IMAGE_DB is ok")
            except Exception:
                log.exception("REDIS_IMAGE_DB is not ok")
            try:
                await redis_helper.execute(
                    redis_conn_set.stream,
                    lambda r: r.execute_command("PING"),
                )
                log.info("REDIS_STREAM_DB is ok")
            except Exception:
                log.exception("REDIS_STREAM_DB is not ok")

    with cli_ctx.logger:
        asyncio.run(_impl())
