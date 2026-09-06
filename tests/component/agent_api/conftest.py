from __future__ import annotations

import secrets
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.data.entity.agent import AGENT_ENTITY_TYPE
from ai.backend.common.data.entity.resource_group import ResourceGroupID, ResourceGroupName
from ai.backend.common.etcd import AsyncEtcd, ConfigScopes
from ai.backend.common.types import HostPortPair
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta
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
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
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
    async_etcd: AsyncEtcd,
    valkey_clients: Any,
    processor_registry: ProcessorRegistry[Any],
) -> AgentProcessors:
    agent_repository = AgentRepository(
        database_engine,
        valkey_image=valkey_clients.image,
        valkey_live=valkey_clients.live,
        valkey_stat=valkey_clients.stat,
        config_provider=config_provider,
        v2_ops_provider=V2DBOpsProvider(database_engine),
    )
    scheduler_repository = SchedulerRepository(
        database_engine,
        ReconcileOpsProvider(database_engine),
        valkey_stat=valkey_clients.stat,
        valkey_schedule=valkey_clients.schedule,
        config_provider=config_provider,
        storage_manager=MagicMock(),
    )
    service = AgentService(
        etcd=async_etcd,
        agent_registry=agent_registry,
        config_provider=config_provider,
        agent_repository=agent_repository,
        scheduler_repository=scheduler_repository,
        scheduling_controller=AsyncMock(),
    )
    return AgentProcessors(
        processor_registry.group(GroupMeta(AGENT_ENTITY_TYPE)),
        service,
        [],
    )


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
    resource_group_name: ResourceGroupName,
    resource_group_id: ResourceGroupID,
) -> AsyncIterator[str]:
    """Insert a test agent row and yield its ID.

    The agent references the scaling_group_name via FK.
    Teardown deletes the agent row (cascade deletes agent_resources).
    """
    agent_id = f"i-test-agent-{secrets.token_hex(6)}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(AgentRow.__table__).values(
                id=agent_id,
                status=AgentStatus.ALIVE,
                region="local",
                scaling_group=resource_group_name,
                resource_group_id=resource_group_id,
                schedulable=True,
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
