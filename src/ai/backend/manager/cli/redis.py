from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import click
import glide

from ai.backend.logging import BraceStyleAdapter
from ai.backend.logging.utils import enforce_debug_logging
from ai.backend.manager.cli.context import redis_ctx

if TYPE_CHECKING:
    from .context import CLIContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.pass_obj
def ping(cli_ctx: CLIContext) -> None:
    """
    Check whether redis database is healthy or not.

    This command temporarily enables the DEBUG-level logging for ai.backend.common.clients.valkey_client
    to help debugging for when there are connection issues, regardless of the logging
    configuration in manager.toml.
    """

    async def _impl() -> None:
        # TODO: Remove redis after migrating to Valkey completely.
        enforce_debug_logging([
            "redis",
            "glide",
            "ai.backend.common.redis_helper",
            "ai.backend.common.clients.valkey_client",
        ])
        async with redis_ctx(cli_ctx) as redis_conn_set:
            try:
                await redis_conn_set.live.ping()
                await redis_conn_set.stat.ping()
                await redis_conn_set.image.ping()
                await redis_conn_set.stream.ping()
                print("Redis is healthy")
            except (glide.ConnectionError, glide.TimeoutError):
                log.exception("ping(): Valkey ping failed")

    asyncio.run(_impl())
