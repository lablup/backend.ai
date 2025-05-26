from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import click
import redis
from tabulate import tabulate

from ai.backend.common import redis_helper
from ai.backend.common.types import RedisConnectionInfo
from ai.backend.logging import BraceStyleAdapter
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
@click.option("--manager-id", help="ID of manager to check status")
@click.argument("scheduler_name")
@click.pass_obj
def last_execution_time(
    cli_ctx: CLIContext, scheduler_name: str, *, manager_id: str | None = None
) -> None:
    """ """

    async def _impl():
        cfg = cli_ctx.get_bootstrap_config()
        _manager_id = manager_id or cfg.manager.id
        async with redis_ctx(cli_ctx) as redis_conn_set:
            redis_key = f"manager.{_manager_id}.{scheduler_name}"
            resp = await redis_helper.execute(redis_conn_set.live, lambda r: r.hgetall(redis_key))
            print(tabulate([(k.decode(), v.decode()) for k, v in resp.items()]))

    asyncio.run(_impl())
