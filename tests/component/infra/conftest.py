from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.data.entity.agent import AGENT_ENTITY_TYPE
from ai.backend.common.data.entity.container_registry import CONTAINER_REGISTRY_ENTITY_TYPE
from ai.backend.common.data.entity.domain import DOMAIN_ENTITY_TYPE
from ai.backend.common.data.entity.etcd_config import ETCD_CONFIG_ENTITY_TYPE
from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE
from ai.backend.common.data.entity.resource_group import RESOURCE_GROUP_ENTITY_TYPE
from ai.backend.common.data.entity.resource_preset import RESOURCE_PRESET_ENTITY_TYPE
from ai.backend.common.data.entity.user import USER_ENTITY_TYPE
from ai.backend.common.etcd import AsyncEtcd
from ai.backend.common.types import ResourceSlot
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import (
    GroupMeta,
)
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.actions.validators.rbac import RBACValidators
from ai.backend.manager.api.rest.etcd.handler import EtcdHandler
from ai.backend.manager.api.rest.etcd.registry import register_etcd_routes
from ai.backend.manager.api.rest.resource.handler import ResourceHandler
from ai.backend.manager.api.rest.resource.registry import register_resource_routes
from ai.backend.manager.api.rest.resource_group.handler import ResourceGroupHandler
from ai.backend.manager.api.rest.resource_group.registry import register_resource_group_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.data.secret.types import KeyProviderType
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.agent.repository import AgentRepository
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.repositories.domain.repository import DomainRepository
from ai.backend.manager.repositories.etcd_config.repository import EtcdConfigRepository
from ai.backend.manager.repositories.ops.v2.container_registry.provider import (
    ContainerRegistryOpsProvider,
)
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.reconciler.provider import ReconcileOpsProvider
from ai.backend.manager.repositories.project.repositories import ProjectRepositories
from ai.backend.manager.repositories.project.repository import ProjectRepository
from ai.backend.manager.repositories.resource_group.repository import ResourceGroupRepository
from ai.backend.manager.repositories.resource_preset.repository import ResourcePresetRepository
from ai.backend.manager.repositories.scheduler.repository import SchedulerRepository
from ai.backend.manager.repositories.user.repository import UserRepository
from ai.backend.manager.secret.pool import KeyProviderPool
from ai.backend.manager.services.agent.processors import AgentProcessors
from ai.backend.manager.services.agent.service import AgentService
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.container_registry.service import ContainerRegistryService
from ai.backend.manager.services.domain.processors import DomainProcessors
from ai.backend.manager.services.domain.service import DomainService
from ai.backend.manager.services.etcd_config.processors import EtcdConfigProcessors
from ai.backend.manager.services.etcd_config.service import EtcdConfigService
from ai.backend.manager.services.project.processors import ProjectProcessors
from ai.backend.manager.services.project.service import ProjectService
from ai.backend.manager.services.resource_group.processors import ResourceGroupProcessors
from ai.backend.manager.services.resource_group.service import ResourceGroupService
from ai.backend.manager.services.resource_preset.processors import ResourcePresetProcessors
from ai.backend.manager.services.resource_preset.service import ResourcePresetService
from ai.backend.manager.services.user.processors import UserProcessors
from ai.backend.manager.services.user.service import UserService


def _create_mock_validators() -> MagicMock:
    mock_rbac = MagicMock(spec=RBACValidators)
    mock_rbac.scope = AsyncMock()
    mock_rbac.single_entity = AsyncMock()
    mock_validators = MagicMock(spec=ActionValidators)
    mock_validators.rbac = mock_rbac
    return mock_validators


@pytest.fixture()
def container_registry_processors(
    database_engine: ExtendedAsyncSAEngine,
    processor_registry: ProcessorRegistry[Any],
) -> ContainerRegistryProcessors:
    repo = ContainerRegistryRepository(
        database_engine, ContainerRegistryOpsProvider(database_engine)
    )
    service = ContainerRegistryService(database_engine, repo)
    return ContainerRegistryProcessors(
        processor_registry.group(GroupMeta(CONTAINER_REGISTRY_ENTITY_TYPE)), service
    )


@pytest.fixture()
def etcd_config_processors(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
    async_etcd: AsyncEtcd,
    valkey_clients: ValkeyClients,
    processor_registry: ProcessorRegistry[Any],
) -> EtcdConfigProcessors:
    repo = EtcdConfigRepository(database_engine)
    service = EtcdConfigService(
        repository=repo,
        config_provider=config_provider,
        etcd=async_etcd,
        valkey_stat=valkey_clients.stat,
    )
    return EtcdConfigProcessors(
        processor_registry.group(GroupMeta(ETCD_CONFIG_ENTITY_TYPE)), service
    )


@pytest.fixture()
def resource_preset_processors(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
    valkey_clients: ValkeyClients,
    processor_registry: ProcessorRegistry[Any],
) -> ResourcePresetProcessors:
    repo = ResourcePresetRepository(database_engine, valkey_clients.stat, config_provider)
    service = ResourcePresetService(repo)
    return ResourcePresetProcessors(
        processor_registry.group(GroupMeta(RESOURCE_PRESET_ENTITY_TYPE)), service
    )


@pytest.fixture()
def agent_processors(
    database_engine: ExtendedAsyncSAEngine,
    async_etcd: AsyncEtcd,
    config_provider: ManagerConfigProvider,
    valkey_clients: ValkeyClients,
    processor_registry: ProcessorRegistry[Any],
) -> AgentProcessors:
    agent_repo = AgentRepository(
        database_engine,
        valkey_clients.image,
        valkey_clients.live,
        valkey_clients.stat,
        config_provider,
        V2DBOpsProvider(database_engine),
    )
    scheduler_repo = SchedulerRepository(
        database_engine,
        ReconcileOpsProvider(database_engine),
        valkey_clients.stat,
        valkey_clients.schedule,
        config_provider,
        MagicMock(),
    )
    service = AgentService(
        etcd=async_etcd,
        agent_registry=AsyncMock(),
        config_provider=config_provider,
        agent_repository=agent_repo,
        scheduler_repository=scheduler_repo,
        scheduling_controller=AsyncMock(),
    )
    return AgentProcessors(
        processor_registry.group(GroupMeta(AGENT_ENTITY_TYPE)),
        service,
        [],
    )


@pytest.fixture()
def project_processors(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
    valkey_clients: ValkeyClients,
    storage_manager: AsyncMock,
    processor_registry: ProcessorRegistry[Any],
) -> ProjectProcessors:
    group_repo = ProjectRepository(
        database_engine,
        V2DBOpsProvider(database_engine),
        config_provider,
        valkey_clients.stat,
        storage_manager,
    )
    group_repos = ProjectRepositories(repository=group_repo)
    service = ProjectService(storage_manager, config_provider, valkey_clients.stat, group_repos)
    return ProjectProcessors(processor_registry.group(GroupMeta(PROJECT_ENTITY_TYPE)), service)


@pytest.fixture()
def user_processors(
    database_engine: ExtendedAsyncSAEngine,
    valkey_clients: ValkeyClients,
    storage_manager: AsyncMock,
    processor_registry: ProcessorRegistry[Any],
) -> UserProcessors:
    user_repo = UserRepository(
        database_engine,
        V2DBOpsProvider(database_engine),
        KeyProviderPool(providers=[], write_provider_type=KeyProviderType.PLAIN),
    )
    service = UserService(storage_manager, valkey_clients.stat, AsyncMock(), user_repo, AsyncMock())
    return UserProcessors(
        processor_registry.group(GroupMeta(USER_ENTITY_TYPE)),
        service,
    )


@pytest.fixture()
def resource_group_processors(
    database_engine: ExtendedAsyncSAEngine,
    processor_registry: ProcessorRegistry[Any],
) -> ResourceGroupProcessors:
    repo = ResourceGroupRepository(database_engine, V2DBOpsProvider(database_engine))
    service = ResourceGroupService(repo, appproxy_client_pool=AsyncMock())
    return ResourceGroupProcessors(
        processor_registry.group(GroupMeta(RESOURCE_GROUP_ENTITY_TYPE)), service
    )


@pytest.fixture()
def domain_processors(
    database_engine: ExtendedAsyncSAEngine,
    processor_registry: ProcessorRegistry[Any],
) -> DomainProcessors:
    """The handler resolves the caller's domain name to its id, so this runs against the DB."""
    service = DomainService(
        repository=DomainRepository(database_engine, V2DBOpsProvider(database_engine))
    )
    return DomainProcessors(processor_registry.group(GroupMeta(DOMAIN_ENTITY_TYPE)), service, [])


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    container_registry_processors: ContainerRegistryProcessors,
    domain_processors: DomainProcessors,
    etcd_config_processors: EtcdConfigProcessors,
    resource_preset_processors: ResourcePresetProcessors,
    agent_processors: AgentProcessors,
    project_processors: ProjectProcessors,
    user_processors: UserProcessors,
    resource_group_processors: ResourceGroupProcessors,
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
                project=project_processors,
                user=user_processors,
                container_registry=container_registry_processors,
            ),
            route_deps,
        ),
        register_resource_group_routes(
            ResourceGroupHandler(
                resource_group=resource_group_processors,
                domain=domain_processors,
                project=project_processors,
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
            sa.select(ProjectRow.__table__.c.name).where(ProjectRow.__table__.c.id == group_fixture)
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
