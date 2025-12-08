from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Protocol

import click
from glide import ConnectionError as GlideConnectionError
from glide import TimeoutError as GlideTimeoutError

from ai.backend.logging import BraceStyleAdapter
from ai.backend.logging.utils import enforce_debug_logging
from ai.backend.manager.cli.context import redis_ctx

if TYPE_CHECKING:
    from .context import CLIContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


class Pingable(Protocol):
    async def ping(self) -> None: ...


@click.group()
def cli() -> None:
    pass


async def _ping(valkey_client: Pingable) -> None:
    try:
        await valkey_client.ping()
    except (GlideConnectionError, GlideTimeoutError):
        log.exception("ping(): Valkey ping failed")


@cli.command()
@click.pass_obj
def ping(cli_ctx: CLIContext) -> None:
    """
    Check whether redis database is healthy or not.

    This command temporarily enables the DEBUG-level logging for ai.backend.common.clients.valkey_client
    to help debugging for when there are connection issues, regardless of the logging
    configuration in manager.toml.
    """

    async def _impl():
        # TODO: Check if this is working as intended
        enforce_debug_logging(["ai.backend.common.clients.valkey_client"])
        async with redis_ctx(cli_ctx) as redis_conn_set:
            await _ping(redis_conn_set.live)
            await _ping(redis_conn_set.stat)
            await _ping(redis_conn_set.image)
            await _ping(redis_conn_set.stream)
            print("Redis is healthy")

    asyncio.run(_impl())
