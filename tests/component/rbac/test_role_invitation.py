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
from ai.backend.client.v2.exceptions import InvalidRequestError, PermissionDeniedError
from ai.backend.client.v2.v2_registry import V2ClientRegistry
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.rbac.request import SearchRoleAssignmentsInput
from ai.backend.common.dto.manager.v2.role_invitation.request import (
    CreateRoleInvitationInput,
    RoleInvitationFilter,
    RoleInvitationOrderBy,
    RoleInvitationOrderField,
    RoleInvitationStateFilter,
    RoleNestedFilter,
    SearchRoleInvitationsInput,
)
from ai.backend.common.dto.manager.v2.role_invitation.response import (
    CreateRoleInvitationPayload,
    RoleInvitationNode,
    SearchRoleInvitationsPayload,
)
from ai.backend.common.dto.manager.v2.role_invitation.types import RoleInvitationStateDTO
from ai.backend.manager.api.adapters.rbac.adapter import RBACAdapter
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
    from tests.component.rbac.conftest import RoleFactory

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
        AdminHandler(
            gql_schema=MagicMock(),
            gql_deps=MagicMock(),
            strawberry_schema=MagicMock(),
            public_strawberry_schema=MagicMock(),
        ),
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
        assert len(result.items) == 1
        node = result.items[0]
        assert isinstance(node, RoleInvitationNode)
        assert node.role_id == target_role.role.id

    async def test_create_invitation_nonexistent_user(
        self,
        admin_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
    ) -> None:
        """Create invitation for non-existent user: 201, empty list (no matching user)."""
        fake_email = f"nobody-{secrets.token_hex(4)}@nonexistent.test"
        result = await admin_v2_registry.role_invitation.create(
            CreateRoleInvitationInput(
                role_id=target_role.role.id,
                emails=[fake_email],
            )
        )
        assert isinstance(result, CreateRoleInvitationPayload)
        assert len(result.items) == 0

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
        assert len(result.items) == 0


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
        search_result = await admin_v2_registry.role_invitation.search_by_role(
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
        search_result = await admin_v2_registry.role_invitation.search_by_role(
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
        result = await admin_v2_registry.role_invitation.search_by_role(
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


class TestSearchInvitationsPagination:
    """Filter and order coverage for role invitation search endpoints."""

    async def test_my_search_filter_state_equals_pending(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """Filter state.equals=pending returns only pending invitations."""
        pending_role = await role_factory()
        rejected_role = await role_factory()
        for role in (pending_role, rejected_role):
            await admin_v2_registry.role_invitation.create(
                CreateRoleInvitationInput(
                    role_id=role.role.id,
                    emails=[regular_user_fixture.email],
                )
            )
        # Reject one invitation so not every invitation is PENDING
        rejected_search = await user_v2_registry.role_invitation.my_search(
            SearchRoleInvitationsInput(
                filter=RoleInvitationFilter(
                    role=RoleNestedFilter(name=StringFilter(equals=rejected_role.role.name))
                )
            )
        )
        assert rejected_search.total_count == 1
        await user_v2_registry.role_invitation.reject(rejected_search.items[0].id)

        result = await user_v2_registry.role_invitation.my_search(
            SearchRoleInvitationsInput(
                filter=RoleInvitationFilter(
                    state=RoleInvitationStateFilter(equals=RoleInvitationStateDTO.PENDING),
                )
            )
        )
        assert result.total_count >= 1
        assert all(inv.state == RoleInvitationStateDTO.PENDING for inv in result.items)
        assert all(inv.role_id != rejected_role.role.id for inv in result.items)

    async def test_role_search_filter_state_in_multiple(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """Filter state.in=[REJECTED, CANCELED] excludes PENDING/ACCEPTED."""
        await admin_v2_registry.role_invitation.create(
            CreateRoleInvitationInput(
                role_id=target_role.role.id,
                emails=[regular_user_fixture.email],
            )
        )
        # Move the only invitation to REJECTED
        my_search = await user_v2_registry.role_invitation.my_search(
            SearchRoleInvitationsInput(
                filter=RoleInvitationFilter(
                    role=RoleNestedFilter(name=StringFilter(equals=target_role.role.name))
                )
            )
        )
        assert my_search.total_count == 1
        await user_v2_registry.role_invitation.reject(my_search.items[0].id)

        result = await admin_v2_registry.role_invitation.search_by_role(
            target_role.role.id,
            SearchRoleInvitationsInput(
                filter=RoleInvitationFilter(
                    state=RoleInvitationStateFilter(
                        in_=[RoleInvitationStateDTO.REJECTED, RoleInvitationStateDTO.CANCELED],
                    ),
                )
            ),
        )
        assert result.total_count == 1
        assert result.items[0].state == RoleInvitationStateDTO.REJECTED

    async def test_my_search_filter_state_not_equals(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """Filter state.not_equals=PENDING excludes pending invitations."""
        pending_role = await role_factory()
        canceled_role = await role_factory()
        for role in (pending_role, canceled_role):
            await admin_v2_registry.role_invitation.create(
                CreateRoleInvitationInput(
                    role_id=role.role.id,
                    emails=[regular_user_fixture.email],
                )
            )
        cancel_target = await admin_v2_registry.role_invitation.search_by_role(
            canceled_role.role.id, SearchRoleInvitationsInput()
        )
        assert cancel_target.total_count == 1
        await admin_v2_registry.role_invitation.cancel(cancel_target.items[0].id)

        result = await user_v2_registry.role_invitation.my_search(
            SearchRoleInvitationsInput(
                filter=RoleInvitationFilter(
                    state=RoleInvitationStateFilter(not_equals=RoleInvitationStateDTO.PENDING),
                )
            )
        )
        assert all(inv.state != RoleInvitationStateDTO.PENDING for inv in result.items)
        assert any(inv.role_id == canceled_role.role.id for inv in result.items)
        assert all(inv.role_id != pending_role.role.id for inv in result.items)

    async def test_my_search_filter_role_name_equals(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """Nested filter role.name.equals narrows results to one role."""
        wanted_role = await role_factory()
        other_role = await role_factory()
        for role in (wanted_role, other_role):
            await admin_v2_registry.role_invitation.create(
                CreateRoleInvitationInput(
                    role_id=role.role.id,
                    emails=[regular_user_fixture.email],
                )
            )
        result = await user_v2_registry.role_invitation.my_search(
            SearchRoleInvitationsInput(
                filter=RoleInvitationFilter(
                    role=RoleNestedFilter(name=StringFilter(equals=wanted_role.role.name)),
                )
            )
        )
        assert result.total_count == 1
        assert result.items[0].role_id == wanted_role.role.id

    async def test_my_search_filter_role_name_contains(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """Nested filter role.name.contains returns matches by substring."""
        unique_token = secrets.token_hex(3)
        prefixed_role = await role_factory(name=f"filter-contains-{unique_token}")
        other_role = await role_factory()
        for role in (prefixed_role, other_role):
            await admin_v2_registry.role_invitation.create(
                CreateRoleInvitationInput(
                    role_id=role.role.id,
                    emails=[regular_user_fixture.email],
                )
            )
        result = await user_v2_registry.role_invitation.my_search(
            SearchRoleInvitationsInput(
                filter=RoleInvitationFilter(
                    role=RoleNestedFilter(name=StringFilter(contains=unique_token)),
                )
            )
        )
        assert result.total_count == 1
        assert result.items[0].role_id == prefixed_role.role.id

    async def test_my_search_filter_and_combines_conditions(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """AND combines state and role filters — only rows matching both remain."""
        matching_role = await role_factory()
        other_role = await role_factory()
        for role in (matching_role, other_role):
            await admin_v2_registry.role_invitation.create(
                CreateRoleInvitationInput(
                    role_id=role.role.id,
                    emails=[regular_user_fixture.email],
                )
            )
        result = await user_v2_registry.role_invitation.my_search(
            SearchRoleInvitationsInput(
                filter=RoleInvitationFilter(
                    AND=[
                        RoleInvitationFilter(
                            state=RoleInvitationStateFilter(equals=RoleInvitationStateDTO.PENDING),
                        ),
                        RoleInvitationFilter(
                            role=RoleNestedFilter(
                                name=StringFilter(equals=matching_role.role.name)
                            ),
                        ),
                    ]
                )
            )
        )
        assert result.total_count == 1
        assert result.items[0].role_id == matching_role.role.id
        assert result.items[0].state == RoleInvitationStateDTO.PENDING

    async def test_role_search_order_created_at_asc_vs_desc(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        admin_user_fixture: UserFixtureData,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """Order by created_at ASC returns oldest first; DESC reverses the order."""
        # Create two invitations at distinct timestamps for the same role
        await admin_v2_registry.role_invitation.create(
            CreateRoleInvitationInput(
                role_id=target_role.role.id,
                emails=[regular_user_fixture.email],
            )
        )
        await admin_v2_registry.role_invitation.create(
            CreateRoleInvitationInput(
                role_id=target_role.role.id,
                emails=[admin_user_fixture.email],
            )
        )
        asc = await admin_v2_registry.role_invitation.search_by_role(
            target_role.role.id,
            SearchRoleInvitationsInput(
                order=[
                    RoleInvitationOrderBy(
                        field=RoleInvitationOrderField.CREATED_AT,
                        direction=OrderDirection.ASC,
                    )
                ],
            ),
        )
        desc = await admin_v2_registry.role_invitation.search_by_role(
            target_role.role.id,
            SearchRoleInvitationsInput(
                order=[
                    RoleInvitationOrderBy(
                        field=RoleInvitationOrderField.CREATED_AT,
                        direction=OrderDirection.DESC,
                    )
                ],
            ),
        )
        assert asc.total_count >= 2
        assert desc.total_count >= 2
        # Same result set, reversed cursor order
        assert [inv.id for inv in asc.items] == list(reversed([inv.id for inv in desc.items]))
        # ASC: non-decreasing timestamps
        asc_ts = [inv.created_at for inv in asc.items]
        assert asc_ts == sorted(asc_ts)

    async def test_role_search_order_state(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
        admin_user_fixture: UserFixtureData,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """Order by state ASC produces a non-decreasing state sequence."""
        role = await role_factory()
        await admin_v2_registry.role_invitation.create(
            CreateRoleInvitationInput(
                role_id=role.role.id,
                emails=[regular_user_fixture.email],
            )
        )
        await admin_v2_registry.role_invitation.create(
            CreateRoleInvitationInput(
                role_id=role.role.id,
                emails=[admin_user_fixture.email],
            )
        )
        # Cancel one so the two invitations have different states.
        listed = await admin_v2_registry.role_invitation.search_by_role(
            role.role.id, SearchRoleInvitationsInput()
        )
        assert listed.total_count == 2
        await admin_v2_registry.role_invitation.cancel(listed.items[0].id)

        result = await admin_v2_registry.role_invitation.search_by_role(
            role.role.id,
            SearchRoleInvitationsInput(
                order=[
                    RoleInvitationOrderBy(
                        field=RoleInvitationOrderField.STATE,
                        direction=OrderDirection.ASC,
                    )
                ],
            ),
        )
        assert result.total_count == 2
        states = [inv.state.value for inv in result.items]
        assert states == sorted(states)

    async def test_role_search_pagination_limit_offset(
        self,
        admin_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        admin_user_fixture: UserFixtureData,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """limit/offset walks through a stable-ordered page window without overlap."""
        for user in (admin_user_fixture, regular_user_fixture):
            await admin_v2_registry.role_invitation.create(
                CreateRoleInvitationInput(
                    role_id=target_role.role.id,
                    emails=[user.email],
                )
            )
        order = [
            RoleInvitationOrderBy(
                field=RoleInvitationOrderField.CREATED_AT,
                direction=OrderDirection.ASC,
            )
        ]
        first_page = await admin_v2_registry.role_invitation.search_by_role(
            target_role.role.id,
            SearchRoleInvitationsInput(limit=1, offset=0, order=order),
        )
        second_page = await admin_v2_registry.role_invitation.search_by_role(
            target_role.role.id,
            SearchRoleInvitationsInput(limit=1, offset=1, order=order),
        )
        assert first_page.total_count >= 2
        assert len(first_page.items) == 1
        assert len(second_page.items) == 1
        assert first_page.items[0].id != second_page.items[0].id
        assert first_page.items[0].created_at <= second_page.items[0].created_at


class TestAdminSearchInvitations:
    """admin_search — scope-less, superadmin only."""

    async def test_admin_search_returns_all_invitations_across_roles(
        self,
        admin_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
        admin_user_fixture: UserFixtureData,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """Superadmin sees invitations spanning multiple roles without scope arg."""
        role_a = await role_factory()
        role_b = await role_factory()
        for role, user in (
            (role_a, regular_user_fixture),
            (role_b, admin_user_fixture),
        ):
            await admin_v2_registry.role_invitation.create(
                CreateRoleInvitationInput(
                    role_id=role.role.id,
                    emails=[user.email],
                )
            )
        result = await admin_v2_registry.role_invitation.admin_search(SearchRoleInvitationsInput())
        assert isinstance(result, SearchRoleInvitationsPayload)
        role_ids = {inv.role_id for inv in result.items}
        assert role_a.role.id in role_ids
        assert role_b.role.id in role_ids

    async def test_admin_search_respects_filter(
        self,
        admin_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """admin_search honors RoleInvitationFilter (state equals)."""
        role = await role_factory()
        await admin_v2_registry.role_invitation.create(
            CreateRoleInvitationInput(
                role_id=role.role.id,
                emails=[regular_user_fixture.email],
            )
        )
        scoped = await admin_v2_registry.role_invitation.search_by_role(
            role.role.id, SearchRoleInvitationsInput()
        )
        assert scoped.total_count == 1
        await admin_v2_registry.role_invitation.cancel(scoped.items[0].id)

        result = await admin_v2_registry.role_invitation.admin_search(
            SearchRoleInvitationsInput(
                filter=RoleInvitationFilter(
                    state=RoleInvitationStateFilter(equals=RoleInvitationStateDTO.CANCELED),
                    role=RoleNestedFilter(name=StringFilter(equals=role.role.name)),
                )
            )
        )
        assert result.total_count == 1
        assert result.items[0].state == RoleInvitationStateDTO.CANCELED
        assert result.items[0].role_id == role.role.id

    async def test_admin_search_denies_regular_user(
        self,
        user_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular user hitting POST /v2/role-invitations/search is rejected by superadmin_required."""
        with pytest.raises(PermissionDeniedError):
            await user_v2_registry.role_invitation.admin_search(SearchRoleInvitationsInput())


class TestRoleScopedSearchNonAdmin:
    """role_search — now RBAC scope-validated, non-admin callers allowed by auth_required."""

    async def test_regular_user_can_call_role_search(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """Regular user (not superadmin) may invoke role_search; RBAC scope validator gates access.

        In component tests the rbac.scope validator is mocked (see
        ``permission_controller_processors`` fixture), so the call succeeds without
        admin privileges — verifying that the endpoint itself is no longer gated by
        ``superadmin_required``.
        """
        await admin_v2_registry.role_invitation.create(
            CreateRoleInvitationInput(
                role_id=target_role.role.id,
                emails=[regular_user_fixture.email],
            )
        )
        result = await user_v2_registry.role_invitation.search_by_role(
            target_role.role.id, SearchRoleInvitationsInput()
        )
        assert isinstance(result, SearchRoleInvitationsPayload)
        assert all(inv.role_id == target_role.role.id for inv in result.items)


class TestMySentSearchInvitations:
    """my_sent_search — invitations sent by the current authenticated user."""

    async def test_my_sent_search_returns_invitations_sent_by_caller(
        self,
        admin_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        admin_user_fixture: UserFixtureData,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """Inviter sees only invitations they created."""
        await admin_v2_registry.role_invitation.create(
            CreateRoleInvitationInput(
                role_id=target_role.role.id,
                emails=[regular_user_fixture.email],
            )
        )
        result = await admin_v2_registry.role_invitation.my_sent_search(
            SearchRoleInvitationsInput()
        )
        assert isinstance(result, SearchRoleInvitationsPayload)
        assert result.total_count == 1
        assert all(inv.inviter_user_id == admin_user_fixture.user_uuid for inv in result.items)

    async def test_my_sent_search_excludes_received_invitations(
        self,
        admin_v2_registry: V2ClientRegistry,
        user_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """Invitee (not inviter) sees nothing in my_sent_search for an invitation they received."""
        await admin_v2_registry.role_invitation.create(
            CreateRoleInvitationInput(
                role_id=target_role.role.id,
                emails=[regular_user_fixture.email],
            )
        )
        sent = await user_v2_registry.role_invitation.my_sent_search(SearchRoleInvitationsInput())
        # Regular user has not sent any invitation — my_sent must be strictly empty.
        assert sent.total_count == 0
        assert sent.items == []

    async def test_my_sent_search_respects_filter_and_order(
        self,
        admin_v2_registry: V2ClientRegistry,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
        admin_user_fixture: UserFixtureData,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        """my_sent_search honors RoleInvitationFilter and RoleInvitationOrderBy."""
        role_a = await role_factory()
        role_b = await role_factory()
        for role in (role_a, role_b):
            await admin_v2_registry.role_invitation.create(
                CreateRoleInvitationInput(
                    role_id=role.role.id,
                    emails=[regular_user_fixture.email],
                )
            )
        filtered = await admin_v2_registry.role_invitation.my_sent_search(
            SearchRoleInvitationsInput(
                filter=RoleInvitationFilter(
                    role=RoleNestedFilter(name=StringFilter(equals=role_a.role.name)),
                )
            )
        )
        assert filtered.total_count == 1
        assert filtered.items[0].role_id == role_a.role.id
        assert filtered.items[0].inviter_user_id == admin_user_fixture.user_uuid

        ordered = await admin_v2_registry.role_invitation.my_sent_search(
            SearchRoleInvitationsInput(
                order=[
                    RoleInvitationOrderBy(
                        field=RoleInvitationOrderField.CREATED_AT,
                        direction=OrderDirection.ASC,
                    )
                ],
            )
        )
        ts = [inv.created_at for inv in ordered.items]
        assert ts == sorted(ts)
