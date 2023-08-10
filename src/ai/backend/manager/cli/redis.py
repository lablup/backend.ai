from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import click
import redis

from ai.backend.common import redis_helper
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.types import RedisConnectionInfo
from ai.backend.manager.cli.context import redis_ctx

if TYPE_CHECKING:
    from .context import CLIContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))  # type: ignore[name-defined]


@click.group()
def cli() -> None:
    pass


async def _ping(redis_conn: RedisConnectionInfo) -> None:
    try:
        await redis_helper.execute(redis_conn, lambda r: r.execute_command("PING"))
    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
        log.exception(f"ping(): Redis ping failed: {e}")


@cli.command()
@click.pass_obj
def ping(cli_ctx: CLIContext) -> None:
    """
    Check whether redis database is healthy or not.
    """

    async def _impl():
        async with redis_ctx(cli_ctx) as redis_conn_set:
            await _ping(redis_conn_set.live)
            await _ping(redis_conn_set.stat)
            await _ping(redis_conn_set.image)
            await _ping(redis_conn_set.stream)
            log.info("Redis is healthy")

    with cli_ctx.logger:
        asyncio.run(_impl())
