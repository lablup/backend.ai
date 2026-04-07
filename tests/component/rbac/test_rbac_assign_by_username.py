"""Component tests for POST /v2/rbac/assignments/assign-by-username."""

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
from ai.backend.common.dto.manager.v2.group.request import AssignUsersToRoleByUsernameInput
from ai.backend.common.dto.manager.v2.group.response import AssignUsersToRoleByUsernamePayload
from ai.backend.manager.api.adapters.rbac import RBACAdapter
from ai.backend.manager.api.rest.admin.handler import AdminHandler
from ai.backend.manager.api.rest.admin.registry import register_admin_routes
from ai.backend.manager.api.rest.rbac.handler import RBACHandler
from ai.backend.manager.api.rest.rbac.registry import register_rbac_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.rbac.handler import V2RBACHandler
from ai.backend.manager.api.rest.v2.rbac.registry import register_v2_rbac_routes
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.group.db_source import GroupDBSource
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
    # Build a partial mock of GroupRepository: only resolve + assign use real DB
    db_source = GroupDBSource(database_engine)
    group_repo = MagicMock()
    group_repo.resolve_users_by_username = db_source.resolve_users_by_username
    group_repo.assign_users_to_project = db_source.assign_users_to_project
    service = PermissionControllerService(
        repo, group_repository=group_repo, rbac_action_registry=[]
    )
    validators = MagicMock()
    validators.rbac.scope.validate = AsyncMock()
    validators.rbac.single_entity.validate = AsyncMock()
    return PermissionControllerProcessors(
        service=service, action_monitors=[], validators=validators
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    permission_controller_processors: PermissionControllerProcessors,
) -> list[RouteRegistry]:
    """Register v1 RBAC (for role creation) and v2 RBAC (for assign-by-username) routes."""
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


class TestAssignRoleByUsername:
    """POST /v2/rbac/assignments/assign-by-username component tests."""

    async def test_assign_by_email_success(
        self,
        admin_registry: BackendAIClientRegistry,
        admin_v2_registry: V2ClientRegistry,
        admin_user_fixture: UserFixtureData,
        group_fixture: uuid.UUID,
        role_factory: RoleFactory,
        db_engine: SAEngine,
    ) -> None:
        """Assigning by email resolves and assigns the user."""
        role = await role_factory()
        result = await admin_v2_registry.rbac.assign_role_by_username(
            AssignUsersToRoleByUsernameInput(
                names=[admin_user_fixture.email],
                role_id=role.role.id,
                project_id=group_fixture,
            ),
        )
        assert isinstance(result, AssignUsersToRoleByUsernamePayload)
        assert result.assigned_count == 1

        # Verify role assignment in DB
        async with db_engine.begin() as conn:
            rows = (
                await conn.execute(
                    sa.select(UserRoleRow.__table__).where(
                        UserRoleRow.__table__.c.user_id == admin_user_fixture.user_uuid,
                        UserRoleRow.__table__.c.role_id == role.role.id,
                    )
                )
            ).fetchall()
            assert len(rows) == 1

    async def test_nonexistent_name_assigns_zero(
        self,
        admin_v2_registry: V2ClientRegistry,
        group_fixture: uuid.UUID,
        role_factory: RoleFactory,
    ) -> None:
        """Non-existent names result in zero assignments."""
        role = await role_factory()
        result = await admin_v2_registry.rbac.assign_role_by_username(
            AssignUsersToRoleByUsernameInput(
                names=["nonexistent@nowhere.com"],
                role_id=role.role.id,
                project_id=group_fixture,
            ),
        )
        assert result.assigned_count == 0

    async def test_mixed_valid_and_invalid_names(
        self,
        admin_registry: BackendAIClientRegistry,
        admin_v2_registry: V2ClientRegistry,
        admin_user_fixture: UserFixtureData,
        group_fixture: uuid.UUID,
        role_factory: RoleFactory,
    ) -> None:
        """Only valid names are assigned; invalid names are silently skipped."""
        role = await role_factory()
        result = await admin_v2_registry.rbac.assign_role_by_username(
            AssignUsersToRoleByUsernameInput(
                names=[admin_user_fixture.email, "ghost@nowhere.com"],
                role_id=role.role.id,
                project_id=group_fixture,
            ),
        )
        assert result.assigned_count == 1
