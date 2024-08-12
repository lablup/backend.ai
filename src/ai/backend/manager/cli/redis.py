from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import click
import redis

from ai.backend.common import redis_helper
from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.logging_utils import enforce_debug_logging
from ai.backend.common.types import RedisConnectionInfo
from ai.backend.manager.cli.context import redis_ctx

if TYPE_CHECKING:
    from .context import CLIContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@click.group()
def cli() -> None:
    pass


async def _ping(redis_conn: RedisConnectionInfo) -> None:
    try:
        await redis_helper.execute(redis_conn, lambda r: r.execute_command("PING"))
    except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
        log.exception("ping(): Redis ping failed")


@cli.command()
@click.pass_obj
def ping(cli_ctx: CLIContext) -> None:
    """
    Check whether redis database is healthy or not.

    This command temporarily enables the DEBUG-level logging for ai.backend.common.redis_helper
    and redis-py to help debugging for when there are connection issues, regardless of the logging
    configuration in manager.toml.
    """

    async def _impl():
        enforce_debug_logging(["redis", "ai.backend.common.redis_helper"])
        async with redis_ctx(cli_ctx) as redis_conn_set:
            await _ping(redis_conn_set.live)
            await _ping(redis_conn_set.stat)
            await _ping(redis_conn_set.image)
            await _ping(redis_conn_set.stream)
            print("Redis is healthy")

    asyncio.run(_impl())
