from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator
from typing import Any, cast, override

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.container_registry import ContainerRegistryType
from ai.backend.common.data.entity.container_registry import ContainerRegistryEntityType
from ai.backend.common.data.entity.project import ProjectEntityType
from ai.backend.manager.actions.registry.registry import ProcessorRegistry
from ai.backend.manager.actions.registry.types import GroupMeta
from ai.backend.manager.api.rest.group.handler import GroupHandler
from ai.backend.manager.api.rest.group.registry import register_group_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.clients.container_registry.harbor import (
    AbstractPerProjectRegistryQuotaClient,
    HarborAuthArgs,
    HarborProjectInfo,
    PerProjectContainerRegistryQuotaClientPool,
)
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.container_registry import ContainerRegistryRow
from ai.backend.manager.models.project import ProjectRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.repositories.container_registry_quota.repository import (
    PerProjectRegistryQuotaRepository,
)
from ai.backend.manager.repositories.ops.v2.provider import V2DBOpsProvider
from ai.backend.manager.repositories.ops.v2.relation.provider import RelationOpsProvider
from ai.backend.manager.repositories.project.repositories import ProjectRepositories
from ai.backend.manager.repositories.project.repository import ProjectRepository
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.container_registry.service import ContainerRegistryService
from ai.backend.manager.services.project.service import ProjectService
from ai.backend.testutils.fixtures import DomainFixtureData


class InMemoryQuotaClient:
    """In-memory Harbor quota client for component tests (duck-typed).

    Does not inherit AbstractPerProjectRegistryQuotaClient because the abstract
    read_quota() returns int, but the API response model
    (ReadRegistryQuotaResponse.result) is int | None. This fixture mirrors
    the expected API behaviour: None when no quota is configured.
    """

    def __init__(self) -> None:
        self._store: dict[str, int] = {}

    async def create_quota(
        self, project_info: HarborProjectInfo, quota: int, auth_args: HarborAuthArgs
    ) -> None:
        self._store[project_info.project] = quota

    async def read_quota(
        self, project_info: HarborProjectInfo, auth_args: HarborAuthArgs
    ) -> int | None:
        return self._store.get(project_info.project)

    async def update_quota(
        self, project_info: HarborProjectInfo, quota: int, auth_args: HarborAuthArgs
    ) -> None:
        self._store[project_info.project] = quota

    async def delete_quota(
        self, project_info: HarborProjectInfo, auth_args: HarborAuthArgs
    ) -> None:
        self._store.pop(project_info.project, None)


class InMemoryQuotaClientPool(PerProjectContainerRegistryQuotaClientPool):
    _client: InMemoryQuotaClient

    def __init__(self) -> None:
        self._client = InMemoryQuotaClient()

    @override
    def make_client(self, type_: ContainerRegistryType) -> AbstractPerProjectRegistryQuotaClient:
        return cast(AbstractPerProjectRegistryQuotaClient, self._client)


@pytest.fixture()
def container_registry_processors(
    database_engine: ExtendedAsyncSAEngine,
    processor_registry: ProcessorRegistry[Any],
) -> ContainerRegistryProcessors:
    repo = ContainerRegistryRepository(database_engine, RelationOpsProvider(database_engine))
    service = ContainerRegistryService(
        database_engine,
        repo,
        PerProjectRegistryQuotaRepository(database_engine),
        InMemoryQuotaClientPool(),
    )
    return ContainerRegistryProcessors(
        processor_registry.group(GroupMeta(ContainerRegistryEntityType())), service
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    container_registry_processors: ContainerRegistryProcessors,
) -> list[RouteRegistry]:
    """Load only the modules required for group-domain tests."""
    return [
        register_group_routes(
            GroupHandler(container_registry=container_registry_processors),
            route_deps,
        ),
    ]


@pytest.fixture()
def group_repository(
    database_engine: ExtendedAsyncSAEngine,
    config_provider: ManagerConfigProvider,
    storage_manager: StorageSessionManager,
    valkey_clients: ValkeyClients,
) -> ProjectRepository:
    """Provide a ProjectRepository backed by the real test database."""
    return ProjectRepository(
        db=database_engine,
        v2_ops_provider=V2DBOpsProvider(database_engine),
        config_provider=config_provider,
        valkey_stat_client=valkey_clients.stat,
        storage_manager=storage_manager,
    )


@pytest.fixture()
def group_service(
    group_repository: ProjectRepository,
    storage_manager: StorageSessionManager,
    config_provider: ManagerConfigProvider,
    valkey_clients: ValkeyClients,
) -> ProjectService:
    """Provide a ProjectService backed by the real test database."""
    group_repositories = ProjectRepositories(repository=group_repository)
    return ProjectService(
        storage_manager=storage_manager,
        config_provider=config_provider,
        valkey_stat_client=valkey_clients.stat,
        group_repositories=group_repositories,
    )


@pytest.fixture()
async def target_group(
    db_engine: SAEngine,
    domain_fixture: DomainFixtureData,
    resource_policy_fixture: str,
) -> AsyncIterator[uuid.UUID]:
    """Insert a test group (project) bound to a HARBOR2 registry and yield its UUID."""
    group_id = uuid.uuid4()
    group_name = f"group-{secrets.token_hex(6)}"
    registry_id = uuid.uuid4()
    registry_name = f"harbor-{registry_id.hex[:8]}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(ContainerRegistryRow.__table__).values(
                id=registry_id,
                url="https://harbor.test.local",
                registry_name=registry_name,
                type=ContainerRegistryType.HARBOR2,
                project=group_name,
            )
        )
        await conn.execute(
            sa.insert(ProjectRow.__table__).values(
                id=group_id,
                name=group_name,
                description=f"Test group {group_name}",
                is_active=True,
                domain_name=domain_fixture.domain_name,
                resource_policy=resource_policy_fixture,
                container_registry={"registry": registry_name, "project": group_name},
            )
        )
        virtual_entity_id = uuid.uuid4()
        await conn.execute(
            sa.insert(VirtualEntityRow.__table__).values(
                id=virtual_entity_id,
                entity_type=ProjectEntityType(),
                entity_id=group_id,
            )
        )
        await conn.execute(
            sa.insert(EntityMembershipRow.__table__).values(
                virtual_entity_id=virtual_entity_id,
                member_entity_id=virtual_entity_id,
                capped=False,
            )
        )
        await conn.execute(
            sa.insert(ScopeBindingRow.__table__).values(
                virtual_entity_id=virtual_entity_id,
                scope_entity_id=virtual_entity_id,
                permission_cap=None,
            )
        )
    yield group_id
    async with db_engine.begin() as conn:
        await conn.execute(
            VirtualEntityRow.__table__.delete().where(
                VirtualEntityRow.__table__.c.entity_type == ProjectEntityType(),
                VirtualEntityRow.__table__.c.entity_id == group_id,
            )
        )
        await conn.execute(
            ProjectRow.__table__.delete().where(ProjectRow.__table__.c.id == group_id)
        )
        await conn.execute(
            ContainerRegistryRow.__table__.delete().where(
                ContainerRegistryRow.__table__.c.id == registry_id
            )
        )
