from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import click
from alembic.config import Config

from ai.backend.common.logging import BraceStyleAdapter
from ai.backend.common.logging_utils import enforce_debug_logging
from ai.backend.common.types import AgentId

if TYPE_CHECKING:
    from .context import CLIContext

log = BraceStyleAdapter(logging.getLogger(__spec__.name))


@click.group()
def cli() -> None:
    pass


@cli.command()
@click.argument("agent_id", type=str)
@click.option(
    "-f",
    "--alembic-config",
    default="alembic.ini",
    metavar="PATH",
    type=click.Path(exists=True, dir_okay=False),
    help="The path to Alembic config file. [default: alembic.ini]",
)
@click.option(
    "-t",
    "--timeout",
    default=10.0,
    type=float,
    help="The timeout to wait until declaring failure. [default: 10.0]",
)
@click.pass_obj
def ping(cli_ctx: CLIContext, agent_id: str, alembic_config: str, timeout: float) -> None:
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

    from ..agent_cache import AgentRPCCache
    from ..models.utils import create_async_engine

    async def _impl():
        manager_public_key, manager_secret_key = load_certificate(
            cli_ctx.local_config["manager"]["rpc-auth-manager-keypair"]
        )
        assert manager_secret_key is not None
        alembic_cfg = Config(alembic_config)
        sa_url = alembic_cfg.get_main_option("sqlalchemy.url")
        db = create_async_engine(sa_url)
        agent_cache = AgentRPCCache(
            db,
            manager_public_key=PublicKey(manager_public_key),
            manager_secret_key=SecretKey(manager_secret_key),
        )
        try:
            log.info("Contacting ag:{} ...", agent_id)
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
        except asyncio.TimeoutError:
            log.error("Timeout occurred while reading the response from ag:{}", agent_id)
        except Exception:
            log.exception("Exception occurred while reading the response from ag:{}", agent_id)
        finally:
            await db.dispose()

    asyncio.run(_impl())
