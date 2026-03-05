from __future__ import annotations

import secrets
from collections.abc import AsyncIterator
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.types import HostPortPair, ResourceSlot
from ai.backend.manager.agent_cache import AgentRPCCache
from ai.backend.manager.api.rest.agent.handler import AgentHandler
from ai.backend.manager.api.rest.agent.registry import register_agent_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.agent.types import AgentStatus
from ai.backend.manager.models.agent.row import AgentRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.registry import AgentRegistry
from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.services.agent.processors import AgentProcessors
from ai.backend.manager.services.agent.service import AgentService


@pytest.fixture()
def async_etcd(
    bootstrap_config: Any,
) -> AsyncEtcd:
    etcd_config = bootstrap_config.etcd
    etcd_addr = etcd_config.addr
    if isinstance(etcd_addr, list):
        addrs: HostPortPair | list[HostPortPair] = [
            HostPortPair(host=a.host, port=a.port) for a in etcd_addr
        ]
    else:
        addrs = HostPortPair(host=etcd_addr.host, port=etcd_addr.port)
    return AsyncEtcd(
        addrs=addrs,
        namespace=etcd_config.namespace,
        scope_prefix_map={
            ConfigScopes.GLOBAL: "global",
            ConfigScopes.SGROUP: "sgroup/default",
            ConfigScopes.NODE: "node/test",
        },
    )


@pytest.fixture()
def agent_processors(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
    agent_registry: AgentRegistry,
    agent_cache: AgentRPCCache,
    hook_plugin_ctx: HookPluginContext,
    event_producer: EventProducer,
    async_etcd: AsyncEtcd,
    valkey_clients: Any,
) -> AgentProcessors:
    agent_repository = AgentRepository(
        database_engine,
        valkey_image=valkey_clients.image,
        valkey_live=valkey_clients.live,
        valkey_stat=valkey_clients.stat,
        config_provider=config_provider,
    )
    scheduler_repository = SchedulerRepository(
        database_engine,
        valkey_stat=valkey_clients.stat,
        config_provider=config_provider,
    )
    service = AgentService(
        etcd=async_etcd,
        agent_registry=agent_registry,
        config_provider=config_provider,
        agent_repository=agent_repository,
        scheduler_repository=scheduler_repository,
        hook_plugin_ctx=hook_plugin_ctx,
        event_producer=event_producer,
        agent_cache=agent_cache,
    )
    return AgentProcessors(service=service, action_monitors=[])


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    agent_processors: AgentProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for agent-api-domain tests."""
    return [
        register_agent_routes(AgentHandler(agent=agent_processors), route_deps),
    ]


@pytest.fixture()
async def agent_fixture(
    db_engine: SAEngine,
    scaling_group_fixture: str,
) -> AsyncIterator[str]:
    """Insert a test agent row and yield its ID.

    The agent references the scaling_group_fixture via FK.
    Teardown deletes the agent row (cascade deletes agent_resources).
    """
    agent_id = f"i-test-agent-{secrets.token_hex(6)}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(AgentRow.__table__).values(
                id=agent_id,
                status=AgentStatus.ALIVE,
                region="local",
                scaling_group=scaling_group_fixture,
                schedulable=True,
                available_slots=ResourceSlot({"cpu": "4", "mem": "8589934592"}),
                occupied_slots=ResourceSlot(),
                addr="tcp://127.0.0.1:6011",
                version="24.12.0",
                architecture="x86_64",
                compute_plugins={},
                auto_terminate_abusing_kernel=False,
            )
        )
    yield agent_id
    async with db_engine.begin() as conn:
        await conn.execute(AgentRow.__table__.delete().where(AgentRow.__table__.c.id == agent_id))
