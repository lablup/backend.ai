from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.events.dispatcher import EventProducer
from ai.backend.common.plugin.hook import HookPluginContext
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.api.rest.middleware import auth as _auth_api
from ai.backend.manager.api.rest.resource.handler import ResourceHandler
from ai.backend.manager.api.rest.resource.registry import register_resource_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.repositories.container_registry.db_source.db_source import (
    ContainerRegistryDBSource,
)
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.repositories.group.repositories import GroupRepositories
from ai.backend.manager.repositories.group.repository import GroupRepository
from ai.backend.manager.repositories.resource_preset.repository import ResourcePresetRepository
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.services.agent.processors import AgentProcessors
from ai.backend.manager.services.agent.service import AgentService
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.container_registry.service import ContainerRegistryService
from ai.backend.manager.services.group.processors import GroupProcessors
from ai.backend.manager.services.group.service import GroupService
from ai.backend.manager.services.resource_preset.processors import ResourcePresetProcessors
from ai.backend.manager.services.resource_preset.service import ResourcePresetService
from ai.backend.manager.services.user.processors import UserProcessors
from ai.backend.manager.services.user.service import UserService

# Statically imported so that Pants includes these modules in the test PEX.
_RESOURCE_PRESET_SERVER_SUBAPP_MODULES = (_auth_api,)

PresetFixtureData = dict[str, Any]
PresetFactory = Callable[..., Coroutine[Any, Any, PresetFixtureData]]


@pytest.fixture()
def container_registry_processors(
    database_engine: ExtendedAsyncSAEngine,
) -> ContainerRegistryProcessors:
    db_source = ContainerRegistryDBSource(database_engine)
    repo = ContainerRegistryRepository(db_source)
    service = ContainerRegistryService(database_engine, repo)
    return ContainerRegistryProcessors(
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
def server_module_registries(
    route_deps: RouteDeps,
    resource_preset_processors: ResourcePresetProcessors,
    agent_processors: AgentProcessors,
    group_processors: GroupProcessors,
    user_processors: UserProcessors,
    container_registry_processors: ContainerRegistryProcessors,
) -> list[RouteRegistry]:
    """Load only the resource preset routes for focused testing."""
    return [
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
async def preset_factory(
    db_engine: SAEngine,
) -> AsyncIterator[PresetFactory]:
    """Factory that inserts resource preset rows directly into DB.

    Yields a factory callable and cleans up all created presets on teardown.
    """
    created_ids: list[uuid.UUID] = []

    async def _create(**overrides: Any) -> PresetFixtureData:
        preset_id = uuid.uuid4()
        defaults: dict[str, Any] = {
            "id": preset_id,
            "name": f"test-preset-{preset_id.hex[:8]}",
            "resource_slots": ResourceSlot({"cpu": "2", "mem": "2147483648"}),
            "shared_memory": None,
            "scaling_group_name": None,
        }
        defaults.update(overrides)
        async with db_engine.begin() as conn:
            await conn.execute(sa.insert(ResourcePresetRow.__table__).values(**defaults))
        created_ids.append(defaults["id"])
        return defaults

    yield _create

    async with db_engine.begin() as conn:
        for pid in reversed(created_ids):
            await conn.execute(
                ResourcePresetRow.__table__.delete().where(ResourcePresetRow.__table__.c.id == pid)
            )


@pytest.fixture()
async def target_preset(
    preset_factory: PresetFactory,
) -> PresetFixtureData:
    """Pre-created preset for tests that need an existing preset."""
    return await preset_factory()
