"""Component tests for RBAC role assignment via v2 REST API."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
import yarl

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.exceptions import PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.rbac.request import (
    AssignRoleInput,
    RevokeRoleInput,
    SearchRoleAssignmentsInput,
)
from ai.backend.common.dto.manager.v2.rbac.response import (
    RoleAssignmentNode,
    SearchRoleAssignmentsPayload,
)
from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter
from ai.backend.manager.api.rest.admin.handler import AdminHandler
from ai.backend.manager.api.rest.admin.registry import register_admin_routes
from ai.backend.manager.api.rest.rbac.handler import RBACHandler
from ai.backend.manager.api.rest.rbac.registry import register_rbac_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.rbac.handler import V2RBACHandler
from ai.backend.manager.api.rest.v2.rbac.registry import register_v2_rbac_routes
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
    from ai.backend.common.dto.manager.rbac.response import CreateRoleResponse


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
    """Register both v1 RBAC (for role creation) and v2 RBAC (for assignments) routes."""
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
async def user_v2_registry(
    server: ServerInfo,
    regular_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
    """Create a V2ClientRegistry with regular-user keypair for v2 REST endpoints."""
    registry = await V2ClientRegistry.create(
        ClientConfig(endpoint=yarl.URL(server.url)),
        HMACAuth(
            access_key=regular_user_fixture.keypair.access_key,
            secret_key=regular_user_fixture.keypair.secret_key,
        ),
    )
    try:
        yield registry
    finally:
        await registry.close()


class TestAssignRoleV2:
    """Test role assignment via v2 REST API."""

    async def test_admin_assigns_role(
        self,
        admin_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        admin_user_fixture: UserFixtureData,
    ) -> None:
        result = await admin_v2_registry.rbac.assign_role(
            AssignRoleInput(
                user_id=admin_user_fixture.user_uuid,
                role_id=target_role.role.id,
            )
        )
        assert isinstance(result, RoleAssignmentNode)
        assert result.user_id == admin_user_fixture.user_uuid
        assert result.role_id == target_role.role.id

        # Clean up
        await admin_v2_registry.rbac.revoke_role(
            RevokeRoleInput(
                user_id=admin_user_fixture.user_uuid,
                role_id=target_role.role.id,
            )
        )

    async def test_regular_user_cannot_assign_role(
        self,
        user_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.rbac.assign_role(
                AssignRoleInput(
                    user_id=regular_user_fixture.user_uuid,
                    role_id=target_role.role.id,
                )
            )


class TestRevokeRoleV2:
    """Test role revocation via v2 REST API."""

    async def test_admin_revokes_role(
        self,
        admin_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        admin_user_fixture: UserFixtureData,
    ) -> None:
        # Assign first
        await admin_v2_registry.rbac.assign_role(
            AssignRoleInput(
                user_id=admin_user_fixture.user_uuid,
                role_id=target_role.role.id,
            )
        )
        # Revoke
        result = await admin_v2_registry.rbac.revoke_role(
            RevokeRoleInput(
                user_id=admin_user_fixture.user_uuid,
                role_id=target_role.role.id,
            )
        )
        assert isinstance(result, RoleAssignmentNode)
        assert result.user_id == admin_user_fixture.user_uuid
        assert result.role_id == target_role.role.id

    async def test_regular_user_cannot_revoke_role(
        self,
        user_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.rbac.revoke_role(
                RevokeRoleInput(
                    user_id=regular_user_fixture.user_uuid,
                    role_id=target_role.role.id,
                )
            )


class TestMySearchAssignmentsV2:
    """Test self-service role assignment search via v2 REST API."""

    async def test_user_searches_own_assignments(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        # Admin assigns a role to the regular user
        await admin_v2_registry.rbac.assign_role(
            AssignRoleInput(
                user_id=regular_user_fixture.user_uuid,
                role_id=target_role.role.id,
            )
        )
        try:
            # Regular user searches their own assignments
            result = await user_v2_registry.rbac.my_search_assignments(SearchRoleAssignmentsInput())
            assert isinstance(result, SearchRoleAssignmentsPayload)
            assert result.total_count >= 1
            assert any(a.role_id == target_role.role.id for a in result.items)
            # All results should belong to the current user
            assert all(a.user_id == regular_user_fixture.user_uuid for a in result.items)
        finally:
            # Clean up
            await admin_v2_registry.rbac.revoke_role(
                RevokeRoleInput(
                    user_id=regular_user_fixture.user_uuid,
                    role_id=target_role.role.id,
                )
            )

    async def test_user_does_not_see_other_users_assignments(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        admin_user_fixture: UserFixtureData,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        # Admin assigns a role to the admin user (not the regular user)
        await admin_v2_registry.rbac.assign_role(
            AssignRoleInput(
                user_id=admin_user_fixture.user_uuid,
                role_id=target_role.role.id,
            )
        )
        try:
            # Regular user searches — should NOT see admin's assignment
            result = await user_v2_registry.rbac.my_search_assignments(SearchRoleAssignmentsInput())
            assert all(a.user_id != admin_user_fixture.user_uuid for a in result.items)
        finally:
            # Clean up
            await admin_v2_registry.rbac.revoke_role(
                RevokeRoleInput(
                    user_id=admin_user_fixture.user_uuid,
                    role_id=target_role.role.id,
                )
            )

    async def test_empty_result_when_no_roles_assigned(
        self,
        user_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await user_v2_registry.rbac.my_search_assignments(SearchRoleAssignmentsInput())
        assert isinstance(result, SearchRoleAssignmentsPayload)
        assert result.total_count == 0
        assert result.items == []
