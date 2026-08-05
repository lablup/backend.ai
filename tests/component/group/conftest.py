from __future__ import annotations

import secrets
import uuid
from collections.abc import AsyncIterator
from typing import cast
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.common.data.permission.types import EntityType, ScopeType
from ai.backend.manager.actions.validators import ActionValidators
from ai.backend.manager.api.rest.group.handler import GroupHandler
from ai.backend.manager.api.rest.group.registry import register_group_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.clients.storage_proxy.session_manager import StorageSessionManager
from ai.backend.manager.config.provider import ManagerConfigProvider
from ai.backend.manager.dependencies.infrastructure.redis import ValkeyClients
from ai.backend.manager.models.group import GroupRow
from ai.backend.manager.models.rbac import ProjectScope
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_scope.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_scope.scope_binding import ScopeBindingRow
from ai.backend.manager.models.virtual_scope.virtual_scope import VirtualScopeRow
from ai.backend.manager.repositories.container_registry.repository import (
    ContainerRegistryRepository,
)
from ai.backend.manager.repositories.group.repositories import GroupRepositories
from ai.backend.manager.repositories.group.repository import GroupRepository
from ai.backend.manager.service.container_registry.harbor import (
    AbstractPerProjectContainerRegistryQuotaService,
)
from ai.backend.manager.services.container_registry.processors import ContainerRegistryProcessors
from ai.backend.manager.services.container_registry.service import ContainerRegistryService
from ai.backend.manager.services.group.service import GroupService
from ai.backend.testutils.fixtures import DomainFixtureData


class InMemoryQuotaService:
    """In-memory quota service for component tests (duck-typed).

    Does not inherit AbstractPerProjectContainerRegistryQuotaService because
    the abstract read_quota() returns int, but the API response model
    (ReadRegistryQuotaResponse.result) is int | None. This fixture mirrors
    the expected API behaviour: None when no quota is configured.
    """

    def __init__(self) -> None:
        self._store: dict[uuid.UUID, int] = {}

    async def create_quota(self, scope_id: ProjectScope, quota: int) -> None:
        self._store[scope_id.project_id] = quota

    async def read_quota(self, scope_id: ProjectScope) -> int | None:
        return self._store.get(scope_id.project_id)

    async def update_quota(self, scope_id: ProjectScope, quota: int) -> None:
        self._store[scope_id.project_id] = quota

    async def delete_quota(self, scope_id: ProjectScope) -> None:
        self._store.pop(scope_id.project_id, None)


@pytest.fixture()
def container_registry_processors(
    database_engine: ExtendedAsyncSAEngine,
) -> ContainerRegistryProcessors:
    repo = ContainerRegistryRepository(database_engine)
    quota_service = cast(AbstractPerProjectContainerRegistryQuotaService, InMemoryQuotaService())
    service = ContainerRegistryService(database_engine, repo, quota_service=quota_service)
    return ContainerRegistryProcessors(
        service=service, action_monitors=[], validators=MagicMock(spec=ActionValidators)
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
) -> GroupRepository:
    """Provide a GroupRepository backed by the real test database."""
    return GroupRepository(
        db=database_engine,
        config_provider=config_provider,
        valkey_stat_client=valkey_clients.stat,
        storage_manager=storage_manager,
    )


@pytest.fixture()
def group_service(
    group_repository: GroupRepository,
    storage_manager: StorageSessionManager,
    config_provider: ManagerConfigProvider,
    valkey_clients: ValkeyClients,
) -> GroupService:
    """Provide a GroupService backed by the real test database."""
    group_repositories = GroupRepositories(repository=group_repository)
    return GroupService(
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
    """Insert a test group (project) and yield its UUID."""
    group_id = uuid.uuid4()
    group_name = f"group-{secrets.token_hex(6)}"
    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(GroupRow.__table__).values(
                id=group_id,
                name=group_name,
                description=f"Test group {group_name}",
                is_active=True,
                domain_name=domain_fixture.domain_name,
                resource_policy=resource_policy_fixture,
            )
        )
        virtual_scope_id = uuid.uuid4()
        await conn.execute(
            sa.insert(VirtualScopeRow.__table__).values(
                id=virtual_scope_id,
                scope_type=ScopeType.PROJECT,
                scope_id=group_id,
            )
        )
        await conn.execute(
            sa.insert(EntityMembershipRow.__table__).values(
                virtual_scope_id=virtual_scope_id,
                entity_type=EntityType.PROJECT,
                entity_id=group_id,
                permission_cap=None,
            )
        )
        await conn.execute(
            sa.insert(ScopeBindingRow.__table__).values(
                virtual_scope_id=virtual_scope_id,
                scope_type=ScopeType.PROJECT,
                scope_id=group_id,
                permission_cap=None,
            )
        )
    yield group_id
    async with db_engine.begin() as conn:
        await conn.execute(
            VirtualScopeRow.__table__.delete().where(
                VirtualScopeRow.__table__.c.scope_type == ScopeType.PROJECT,
                VirtualScopeRow.__table__.c.scope_id == group_id,
            )
        )
        await conn.execute(GroupRow.__table__.delete().where(GroupRow.__table__.c.id == group_id))
