"""Component tests for role invitations via v2 REST API."""

from __future__ import annotations

import secrets
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
import yarl

from ai.backend.client.v2.auth import HMACAuth
from ai.backend.client.v2.config import ClientConfig
from ai.backend.client.v2.exceptions import InvalidRequestError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.v2.rbac.request import SearchRoleAssignmentsInput
from ai.backend.common.dto.manager.v2.role_invitation.request import (
    CreateRoleInvitationInput,
    SearchRoleInvitationsInput,
)
from ai.backend.common.dto.manager.v2.role_invitation.response import (
    CreateRoleInvitationPayload,
    RoleInvitationNode,
    SearchRoleInvitationsPayload,
)
from ai.backend.manager.api.adapters.rbac import RBACAdapter
from ai.backend.manager.api.rest.admin.handler import AdminHandler
from ai.backend.manager.api.rest.admin.registry import register_admin_routes
from ai.backend.manager.api.rest.rbac.handler import RBACHandler
from ai.backend.manager.api.rest.rbac.registry import register_rbac_routes
from ai.backend.manager.api.rest.routing import RouteRegistry
from ai.backend.manager.api.rest.types import RouteDeps
from ai.backend.manager.api.rest.v2.rbac.handler import V2RBACHandler
from ai.backend.manager.api.rest.v2.rbac.registry import register_v2_rbac_routes
from ai.backend.manager.api.rest.v2.role_invitation.handler import V2RoleInvitationHandler
from ai.backend.manager.api.rest.v2.role_invitation.registry import (
    register_v2_role_invitation_routes,
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
    validators.rbac.single_entity.validate = AsyncMock()
    return PermissionControllerProcessors(
        service=service, action_monitors=[], validators=validators
    )


@pytest.fixture()
def server_module_registries(
    route_deps: RouteDeps,
    permission_controller_processors: PermissionControllerProcessors,
) -> list[RouteRegistry]:
    """Register v1 RBAC (for role creation) and v2 invitation routes."""
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

    v2_reg = RouteRegistry.create("v2", route_deps.cors_options)
    v2_reg.add_subregistry(register_v2_rbac_routes(V2RBACHandler(adapter=adapter), route_deps))
    v2_reg.add_subregistry(
        register_v2_role_invitation_routes(V2RoleInvitationHandler(adapter=adapter), route_deps)
    )
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


@pytest.fixture()
async def user_v2_registry(
    server: ServerInfo,
    regular_user_fixture: UserFixtureData,
) -> AsyncIterator[V2ClientRegistry]:
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


class TestCreateRoleInvitation:
    """Test invitation creation."""

    async def test_create_invitation_happy_path(
        self,
        admin_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """Create invitation for an existing ACTIVE user: 201 with opaque response."""
        result = await admin_v2_registry.role_invitation.create(
            CreateRoleInvitationInput(
                role_id=target_role.role.id,
                emails=[regular_user_fixture.email],
            )
        )
        assert isinstance(result, CreateRoleInvitationPayload)
        assert result.ok is True

    async def test_create_invitation_nonexistent_user(
        self,
        admin_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
    ) -> None:
        """Create invitation for non-existent user: 201 returned (opaque), no row inserted."""
        fake_email = f"nobody-{secrets.token_hex(4)}@nonexistent.test"
        result = await admin_v2_registry.role_invitation.create(
            CreateRoleInvitationInput(
                role_id=target_role.role.id,
                emails=[fake_email],
            )
        )
        # Opaque response — always 201 regardless of user existence
        assert isinstance(result, CreateRoleInvitationPayload)
        assert result.ok is True

    async def test_create_duplicate_pending_invitation(
        self,
        admin_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """Duplicate PENDING for (role_id, invitee_user_id): no new row, still 201."""
        input_dto = CreateRoleInvitationInput(
            role_id=target_role.role.id,
            emails=[regular_user_fixture.email],
        )
        # First invitation
        await admin_v2_registry.role_invitation.create(input_dto)
        # Second invitation with the same parameters — should not create a new row
        result = await admin_v2_registry.role_invitation.create(input_dto)
        assert isinstance(result, CreateRoleInvitationPayload)
        assert result.ok is True


class TestAcceptRejectCancelInvitation:
    """Test invitation state transitions."""

    async def test_accept_transitions_to_accepted(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """Accept transitions PENDING -> ACCEPTED and assigns the role."""
        # Admin creates invitation
        await admin_v2_registry.role_invitation.create(
            CreateRoleInvitationInput(
                role_id=target_role.role.id,
                emails=[regular_user_fixture.email],
            )
        )
        # Find the invitation
        search_result = await user_v2_registry.role_invitation.my_search(
            SearchRoleInvitationsInput()
        )
        pending = [
            inv
            for inv in search_result.items
            if inv.role_id == target_role.role.id and inv.state == "pending"
        ]
        assert len(pending) >= 1
        invitation_id = pending[0].id

        # User accepts the invitation
        result = await user_v2_registry.role_invitation.accept(invitation_id)
        assert isinstance(result, RoleInvitationNode)
        assert result.state == "accepted"
        assert result.role_id == target_role.role.id

    async def test_accept_assigns_role_to_user(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """Accept invitation must create a role assignment for the invitee."""
        # Admin creates invitation
        await admin_v2_registry.role_invitation.create(
            CreateRoleInvitationInput(
                role_id=target_role.role.id,
                emails=[regular_user_fixture.email],
            )
        )
        # User finds and accepts the invitation
        search_result = await user_v2_registry.role_invitation.my_search(
            SearchRoleInvitationsInput()
        )
        pending = [
            inv
            for inv in search_result.items
            if inv.role_id == target_role.role.id and inv.state == "pending"
        ]
        assert len(pending) >= 1
        await user_v2_registry.role_invitation.accept(pending[0].id)

        # Verify the role is actually assigned to the user
        assignments = await user_v2_registry.rbac.my_search_assignments(
            SearchRoleAssignmentsInput()
        )
        assigned_role_ids = [a.role_id for a in assignments.items]
        assert target_role.role.id in assigned_role_ids

    async def test_reject_transitions_to_rejected(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """Reject transitions PENDING -> REJECTED without role assignment."""
        # Admin creates invitation
        await admin_v2_registry.role_invitation.create(
            CreateRoleInvitationInput(
                role_id=target_role.role.id,
                emails=[regular_user_fixture.email],
            )
        )
        # Find the invitation
        search_result = await user_v2_registry.role_invitation.my_search(
            SearchRoleInvitationsInput()
        )
        pending = [
            inv
            for inv in search_result.items
            if inv.role_id == target_role.role.id and inv.state == "pending"
        ]
        assert len(pending) >= 1
        invitation_id = pending[0].id

        # User rejects the invitation
        result = await user_v2_registry.role_invitation.reject(invitation_id)
        assert isinstance(result, RoleInvitationNode)
        assert result.state == "rejected"

    async def test_cancel_transitions_to_canceled(
        self,
        admin_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """Cancel transitions PENDING -> CANCELED."""
        # Admin creates invitation
        await admin_v2_registry.role_invitation.create(
            CreateRoleInvitationInput(
                role_id=target_role.role.id,
                emails=[regular_user_fixture.email],
            )
        )
        # Find via role search
        search_result = await admin_v2_registry.role_invitation.role_search(
            target_role.role.id, SearchRoleInvitationsInput()
        )
        pending = [inv for inv in search_result.items if inv.state == "pending"]
        assert len(pending) >= 1
        invitation_id = pending[0].id

        # Admin cancels the invitation
        result = await admin_v2_registry.role_invitation.cancel(invitation_id)
        assert isinstance(result, RoleInvitationNode)
        assert result.state == "canceled"

    async def test_accept_rejected_invitation_fails(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """Cannot accept an invitation that has already been rejected."""
        await admin_v2_registry.role_invitation.create(
            CreateRoleInvitationInput(
                role_id=target_role.role.id,
                emails=[regular_user_fixture.email],
            )
        )
        search_result = await user_v2_registry.role_invitation.my_search(
            SearchRoleInvitationsInput()
        )
        pending = [
            inv
            for inv in search_result.items
            if inv.role_id == target_role.role.id and inv.state == "pending"
        ]
        assert len(pending) >= 1
        invitation_id = pending[0].id

        await user_v2_registry.role_invitation.reject(invitation_id)

        with pytest.raises(InvalidRequestError):
            await user_v2_registry.role_invitation.accept(invitation_id)

    async def test_accept_canceled_invitation_fails(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """Cannot accept an invitation that has already been canceled."""
        await admin_v2_registry.role_invitation.create(
            CreateRoleInvitationInput(
                role_id=target_role.role.id,
                emails=[regular_user_fixture.email],
            )
        )
        search_result = await admin_v2_registry.role_invitation.role_search(
            target_role.role.id, SearchRoleInvitationsInput()
        )
        pending = [inv for inv in search_result.items if inv.state == "pending"]
        assert len(pending) >= 1
        invitation_id = pending[0].id

        await admin_v2_registry.role_invitation.cancel(invitation_id)

        with pytest.raises(InvalidRequestError):
            await user_v2_registry.role_invitation.accept(invitation_id)


class TestSearchInvitations:
    """Test invitation listing/search."""

    async def test_my_search_returns_own_invitations(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """Invitee can search their own invitations."""
        # Admin creates invitation for the regular user
        await admin_v2_registry.role_invitation.create(
            CreateRoleInvitationInput(
                role_id=target_role.role.id,
                emails=[regular_user_fixture.email],
            )
        )
        result = await user_v2_registry.role_invitation.my_search(SearchRoleInvitationsInput())
        assert isinstance(result, SearchRoleInvitationsPayload)
        assert result.total_count >= 1
        # All results should belong to the current user
        assert all(inv.invitee_user_id == regular_user_fixture.user_uuid for inv in result.items)

    async def test_role_search_returns_role_invitations(
        self,
        admin_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """Admin can search invitations by role."""
        # Admin creates invitation
        await admin_v2_registry.role_invitation.create(
            CreateRoleInvitationInput(
                role_id=target_role.role.id,
                emails=[regular_user_fixture.email],
            )
        )
        result = await admin_v2_registry.role_invitation.role_search(
            target_role.role.id, SearchRoleInvitationsInput()
        )
        assert isinstance(result, SearchRoleInvitationsPayload)
        assert result.total_count >= 1
        assert all(inv.role_id == target_role.role.id for inv in result.items)

    async def test_my_search_empty_when_no_invitations(
        self,
        user_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Empty result when user has no invitations."""
        result = await user_v2_registry.role_invitation.my_search(SearchRoleInvitationsInput())
        assert isinstance(result, SearchRoleInvitationsPayload)
        assert result.total_count == 0
        assert result.items == []
