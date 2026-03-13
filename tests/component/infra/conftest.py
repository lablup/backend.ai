from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.api.rest.etcd.handler import EtcdHandler
from ai.backend.manager.api.rest.etcd.registry import register_etcd_routes
from ai.backend.manager.api.rest.resource.handler import ResourceHandler
from ai.backend.manager.api.rest.resource.registry import register_resource_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.scaling_group.handler import ScalingGroupHandler
from ai.backend.manager.api.rest.scaling_group.registry import register_scaling_group_routes
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.repositories.etcd_config.repository import EtcdConfigRepository
from ai.backend.manager.repositories.group.repositories import GroupRepositories
from ai.backend.manager.repositories.group.repository import GroupRepository
from ai.backend.manager.repositories.resource_preset.repository import ResourcePresetRepository
from ai.backend.manager.repositories.scaling_group.repository import ScalingGroupRepository
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.services.agent.processors import AgentProcessors
from ai.backend.manager.services.agent.service import AgentService
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.container_registry.service import ContainerRegistryService
from ai.backend.manager.services.etcd_config.processors import EtcdConfigProcessors
from ai.backend.manager.services.etcd_config.service import EtcdConfigService
from ai.backend.manager.services.group.processors import GroupProcessors
from ai.backend.manager.services.group.service import GroupService
from ai.backend.manager.services.resource_preset.processors import ResourcePresetProcessors
from ai.backend.manager.services.resource_preset.service import ResourcePresetService
from ai.backend.manager.services.scaling_group.processors import ScalingGroupProcessors
from ai.backend.manager.services.scaling_group.service import ScalingGroupService
from ai.backend.manager.services.user.processors import UserProcessors
from ai.backend.manager.services.user.service import UserService


@pytest.fixture()
def container_registry_processors(
    database_engine: ExtendedAsyncSAEngine,
) -> ContainerRegistryProcessors:
    repo = ContainerRegistryRepository(database_engine)
    service = ContainerRegistryService(database_engine, repo)
    return ContainerRegistryProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def etcd_config_processors(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
    async_etcd: AsyncEtcd,
    valkey_clients: ValkeyClients,
) -> EtcdConfigProcessors:
    repo = EtcdConfigRepository(database_engine)
    service = EtcdConfigService(
        repository=repo,
        config_provider=config_provider,
        etcd=async_etcd,
        valkey_stat=valkey_clients.stat,
    )
    return EtcdConfigProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def resource_preset_processors(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
    valkey_clients: ValkeyClients,
) -> ResourcePresetProcessors:
    repo = ResourcePresetRepository(database_engine, valkey_clients.stat, config_provider)
    service = ResourcePresetService(repo)
    return ResourcePresetProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def agent_processors(
    database_engine: ExtendedAsyncSAEngine,
    async_etcd: AsyncEtcd,
    config_provider: ManagerConfigProvider,
    hook_plugin_ctx: HookPluginContext,
    event_producer: EventProducer,
    valkey_clients: ValkeyClients,
) -> AgentProcessors:
    agent_repo = AgentRepository(
        database_engine,
        valkey_clients.image,
        valkey_clients.live,
        valkey_clients.stat,
        config_provider,
    )
    scheduler_repo = SchedulerRepository(database_engine, valkey_clients.stat, config_provider)
    service = AgentService(
        etcd=async_etcd,
        agent_registry=AsyncMock(),
        config_provider=config_provider,
        agent_repository=agent_repo,
        scheduler_repository=scheduler_repo,
        hook_plugin_ctx=hook_plugin_ctx,
        event_producer=event_producer,
        agent_cache=AsyncMock(),
    )
    return AgentProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def group_processors(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
    valkey_clients: ValkeyClients,
    storage_manager: AsyncMock,
) -> GroupProcessors:
    group_repo = GroupRepository(
        database_engine, config_provider, valkey_clients.stat, storage_manager
    )
    group_repos = GroupRepositories(repository=group_repo)
    service = GroupService(storage_manager, config_provider, valkey_clients.stat, group_repos)
    return GroupProcessors(
        group_service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def user_processors(
    database_engine: ExtendedAsyncSAEngine,
    valkey_clients: ValkeyClients,
    storage_manager: AsyncMock,
) -> UserProcessors:
    user_repo = UserRepository(database_engine)
    service = UserService(storage_manager, valkey_clients.stat, AsyncMock(), user_repo)
    return UserProcessors(
        user_service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def scaling_group_processors(
    database_engine: ExtendedAsyncSAEngine,
) -> ScalingGroupProcessors:
    repo = ScalingGroupRepository(database_engine)
    service = ScalingGroupService(repo, appproxy_client_pool=AsyncMock())
    return ScalingGroupProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    container_registry_processors: ContainerRegistryProcessors,
    etcd_config_processors: EtcdConfigProcessors,
    resource_preset_processors: ResourcePresetProcessors,
    agent_processors: AgentProcessors,
    group_processors: GroupProcessors,
    user_processors: UserProcessors,
    scaling_group_processors: ScalingGroupProcessors,
    config_provider: ManagerConfigProvider,
) -> list[RouteRegistry]:
    """Load only the modules required for infra-domain tests."""
    return [
        register_etcd_routes(
            EtcdHandler(
                container_registry=container_registry_processors,
                etcd_config=etcd_config_processors,
            ),
            route_deps,
            pidx=0,
            config_provider=config_provider,
        ),
        register_resource_routes(
            ResourceHandler(
                resource_preset=resource_preset_processors,
                agent=agent_processors,
                group=group_processors,
                user=user_processors,
                container_registry=container_registry_processors,
            ),
            route_deps,
        ),
        register_scaling_group_routes(
            ScalingGroupHandler(scaling_group=scaling_group_processors), route_deps
        ),
    ]


@pytest.fixture()
async def group_name_fixture(
    db_engine: SAEngine,
    group_fixture: uuid.UUID,
) -> str:
    """Query the group name from the database for the test group."""
    async with db_engine.begin() as conn:
        result = await conn.execute(
            sa.select(GroupRow.__table__.c.name).where(GroupRow.__table__.c.id == group_fixture)
        )
        row = result.first()
        assert row is not None
        return str(row[0])


@pytest.fixture()
async def resource_preset_fixture(
    db_engine: SAEngine,
) -> AsyncIterator[dict[str, str]]:
    """Insert a test resource preset and yield its metadata.

    Used for list_presets and check_presets tests. Cleaned up after each test.
    """
    preset_id = uuid.uuid4()
    preset_name = f"test-preset-{preset_id.hex[:8]}"
    resource_slots = ResourceSlot({"cpu": "1", "mem": "1073741824"})
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(ResourcePresetRow.__table__).values(
                id=preset_id,
                name=preset_name,
                resource_slots=resource_slots,
                shared_memory=None,
                scaling_group_name=None,
            )
        )
    yield {"id": str(preset_id), "name": preset_name}
    async with db_engine.begin() as conn:
        await conn.execute(
            ResourcePresetRow.__table__.delete().where(
                ResourcePresetRow.__table__.c.id == preset_id
            )
        )
