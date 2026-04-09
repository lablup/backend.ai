"""Component tests for scoped role search via v2 REST API."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
import sqlalchemy as sa
import yarl
from sqlalchemy.ext.asyncio.engine import AsyncEngine as SAEngine

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.rbac.request import SearchRolesInput
from ai.backend.common.dto.manager.v2.rbac.response import AdminSearchRolesPayload
from ai.backend.manager.api.adapters.rbac import RBACAdapter
from ai.backend.manager.api.rest.admin.handler import AdminHandler
from ai.backend.manager.api.rest.admin.registry import register_admin_routes
from ai.backend.manager.api.rest.rbac.handler import RBACHandler
from ai.backend.manager.api.rest.rbac.registry import register_rbac_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.rbac.handler import V2RBACHandler
from ai.backend.manager.api.rest.v2.rbac.registry import register_v2_rbac_routes
from ai.backend.manager.data.permission.types import EntityType, ScopeType
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.services.permission_contoller.processors import (
    PermissionControllerProcessors,
)
from ai.backend.manager.services.permission_contoller.service import PermissionControllerService

if TYPE_CHECKING:
    from tests.component.conftest import ServerInfo, UserFixtureData

    from ai.backend.client.v2.registry import BackendAIClientRegistry

from .conftest import RoleFactory


@pytest.fixture()
def permission_controller_processors(
    database_engine: ExtendedAsyncSAEngine,
) -> PermissionControllerProcessors:
    repo = PermissionControllerRepository(database_engine)
    service = PermissionControllerService(
        repo, group_repository=MagicMock(), rbac_action_registry=[]
    )
    validators = MagicMock()
    validators.rbac.scope.validate = AsyncMock()
    return PermissionControllerProcessors(
        service=service, action_monitors=[], validators=validators
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    permission_controller_processors: PermissionControllerProcessors,
) -> list[RouteRegistry]:
    """Register both v1 RBAC (for role creation) and v2 RBAC (for project search) routes."""
    rbac_registry = register_rbac_routes(
        RBACHandler(permission_controller=permission_controller_processors), route_deps
    )
    admin_registry = register_admin_routes(
        AdminHandler(gql_schema=MagicMock(), gql_deps=MagicMock(), strawberry_schema=MagicMock()),
        route_deps,
        sub_registries=[rbac_registry],
        gql_ws_handler=MagicMock(),
    )

    processors = MagicMock()
    processors.permission_controller = permission_controller_processors
    adapter = RBACAdapter(processors)
    handler = V2RBACHandler(adapter=adapter)
    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_rbac_routes(handler, route_deps))

    return [admin_registry, v2_reg]


@pytest.fixture()
async def admin_v2_registry(
    server: ServerInfo,
    admin_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    """Create a V2ClientRegistry with superadmin keypair for v2 REST endpoints."""
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=admin_user_fixture.keypair.access_key,
            secret_key=admin_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()


@pytest.fixture()
async def role_registered_in_project(
    role_factory: RoleFactory,
    group_fixture: uuid.UUID,
    db_engine: SAEngine,
) -> AsyncIterator[uuid.UUID]:
    """Create a role and register it in the project scope. Yields the role ID."""
    created = await role_factory(name=f"proj-role-{uuid.uuid4().hex[:8]}")
    role_id = created.role.id

    async with db_engine.begin() as conn:
        await conn.execute(
            sa.insert(AssociationScopesEntitiesRow.__table__).values(
                id=uuid.uuid4(),
                scope_type=ScopeType.PROJECT,
                scope_id=str(group_fixture),
                entity_type=EntityType.ROLE,
                entity_id=str(role_id),
            )
        )

    yield role_id

    async with db_engine.begin() as conn:
        await conn.execute(
            AssociationScopesEntitiesRow.__table__.delete().where(
                AssociationScopesEntitiesRow.__table__.c.entity_id == str(role_id),
            )
        )


class TestScopedRoleSearch:
    """Search roles registered in a specific scope."""

    async def test_returns_roles_registered_in_project(
        self,
        admin_registry: BackendAIClientRegistry,
        admin_v2_registry: V2ClientRegistry,
        group_fixture: uuid.UUID,
        role_registered_in_project: uuid.UUID,
    ) -> None:
        """Roles registered in project scope should appear in project search."""
        result = await admin_v2_registry.rbac.project_search_roles(
            group_fixture,
            SearchRolesInput(),
        )
        assert isinstance(result, AdminSearchRolesPayload)
        role_ids = [r.id for r in result.items]
        assert role_registered_in_project in role_ids

    async def test_excludes_roles_not_in_project(
        self,
        admin_registry: BackendAIClientRegistry,
        admin_v2_registry: V2ClientRegistry,
        role_factory: RoleFactory,
        group_fixture: uuid.UUID,
        role_registered_in_project: uuid.UUID,
    ) -> None:
        """Roles NOT registered in project scope should NOT appear in project search."""
        not_in_project = await role_factory(name=f"not-in-proj-{uuid.uuid4().hex[:8]}")

        result = await admin_v2_registry.rbac.project_search_roles(
            group_fixture,
            SearchRolesInput(),
        )
        role_ids = [r.id for r in result.items]
        assert role_registered_in_project in role_ids
        assert not_in_project.role.id not in role_ids

    async def test_empty_project_returns_no_roles(
        self,
        admin_v2_registry: V2ClientRegistry,
        group_fixture: uuid.UUID,
    ) -> None:
        """A project with no registered roles should return an empty list."""
        result = await admin_v2_registry.rbac.project_search_roles(
            group_fixture,
            SearchRolesInput(),
        )
        assert isinstance(result, AdminSearchRolesPayload)
        assert result.items == []
        assert result.total_count == 0
