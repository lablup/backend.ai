from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import click

from ai.backend.common.types import AgentId
from ai.backend.logging.structured import StructuredLogger
from ai.backend.logging.utils import enforce_debug_logging
from ai.backend.manager.cli.alembic_config import (
    ALEMBIC_CONFIG_HELP,
    db_config_loader,
    resolve_alembic_config,
)
from ai.backend.manager.errors.resource import ConfigurationLoadFailed

if TYPE_CHECKING:
    from .context import CLIContext

log = StructuredLogger(logging.getLogger(__spec__.name))


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.argument("agent_id", type=str)
@click.option(
    "-f",
    "--alembic-config",
    default=None,
    metavar="PATH",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help=ALEMBIC_CONFIG_HELP,
)
@click.option(
    "-t",
    "--timeout",
    default=10.0,
    type=float,
    help="The timeout to wait until declaring failure. [default: 10.0]",
)
@click.pass_obj
def ping(cli_ctx: CLIContext, agent_id: str, alembic_config: Path | None, timeout: float) -> None:
    """
    Ping the agent with AGENT_ID to check whether it responds to an RPC call.

    It uses AgentRPCCache to make the actual RPC call, which reads the agent address and public key
    from the PostgreSQL database.  If the target agent have changed its address or public key while
    the manager is *not* running, it may fail even when the agent is alive.

    This command temporarily enables the DEBUG-level logging for ai.backend.manager.agent_cache
    and callosum to help debugging for when there are connection issues, regardless of the logging
    configuration in manager.toml.
    """
    from zmq.auth.certs import load_certificate

    from ai.backend.common.auth import PublicKey, SecretKey
    from ai.backend.manager.agent_cache import AgentRPCCache
    from ai.backend.manager.repositories.db.engine import create_async_engine

    async def _impl() -> None:
        bootstrap_config = await cli_ctx.get_bootstrap_config()
        manager_public_key, manager_secret_key = load_certificate(
            bootstrap_config.manager.rpc_auth_manager_keypair
        )
        if manager_secret_key is None:
            raise ConfigurationLoadFailed("Manager secret key is not available in the keypair")
        resolved = await resolve_alembic_config(alembic_config, db_config_loader(cli_ctx))
        db = create_async_engine(resolved.db_url)
        agent_cache = AgentRPCCache(
            db,
            manager_public_key=PublicKey(manager_public_key),
            manager_secret_key=SecretKey(manager_secret_key),
        )
        try:
            log.info("contacting the agent", agent_id=agent_id)
            enforce_debug_logging(["callosum", "ai.backend.manager.agent_cache"])
            async with agent_cache.rpc_context(
                AgentId(agent_id),
                invoke_timeout=timeout,
            ) as rpc:
                result = await rpc.call.ping("pong")
                print(f"Received response from ag:{agent_id}: {result}")
                # FIXME: Use gather_hwinfo() when we implement get_node_hwinfo() of CPUPlugin and MemoryPlugin like below.
                # result = await rpc.call.gather_hwinfo()
                # print(f"Retrieved ag:{agent_id} hardware information as a health check:")
                # pprint(result)
        except TimeoutError:
            log.error("timed out while reading the response from the agent", agent_id=agent_id)
        except Exception:
            log.exception("failed to read the response from the agent", agent_id=agent_id)
        finally:
            await db.dispose()

    asyncio.run(_impl())
