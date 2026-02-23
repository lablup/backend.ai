from __future__ import annotations

import secrets
import uuid
from collections.abc import Callable, Coroutine
from typing import Any

import pytest
from tests.component.conftest import UserFixtureData

from ai.backend.client.v2.exceptions import NotFoundError, PermissionDeniedError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.rbac.request import (
    AssignRoleRequest,
    CreateRoleRequest,
    DeleteRoleRequest,
    PurgeRoleRequest,
    RevokeRoleRequest,
    RoleFilter,
    SearchRolesRequest,
    SearchScopesRequest,
    SearchUsersAssignedToRoleRequest,
    UpdateRoleRequest,
)
from ai.backend.common.dto.manager.rbac.response import (
    AssignRoleResponse,
    CreateRoleResponse,
    DeleteRoleResponse,
    GetEntityTypesResponse,
    GetRoleResponse,
    GetScopeTypesResponse,
    RevokeRoleResponse,
    SearchRolesResponse,
    SearchScopesResponse,
    SearchUsersAssignedToRoleResponse,
    UpdateRoleResponse,
)
from ai.backend.common.dto.manager.rbac.types import RoleSource, RoleStatus

RoleFactory = Callable[..., Coroutine[Any, Any, CreateRoleResponse]]


class TestRoleCreate:
    @pytest.mark.asyncio
    async def test_admin_creates_role(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        result = await role_factory(
            name=f"test-role-{unique}",
            description=f"Test role {unique}",
        )
        assert isinstance(result, CreateRoleResponse)
        assert result.role.name == f"test-role-{unique}"
        assert result.role.description == f"Test role {unique}"
        assert result.role.source == RoleSource.CUSTOM
        assert result.role.status == RoleStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_admin_creates_role_with_description(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        result = await role_factory(
            name=f"desc-role-{unique}",
            description="A role with a description",
        )
        assert result.role.description == "A role with a description"

    @pytest.mark.asyncio
    async def test_regular_user_cannot_create_role(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        unique = secrets.token_hex(4)
        with pytest.raises(PermissionDeniedError):
            await user_registry.rbac.create_role(
                CreateRoleRequest(
                    name=f"denied-role-{unique}",
                    description="Should be denied",
                )
            )


class TestRoleGet:
    @pytest.mark.asyncio
    async def test_admin_gets_role_by_id(
        self,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
    ) -> None:
        get_result = await admin_registry.rbac.get_role(target_role.role.id)
        assert isinstance(get_result, GetRoleResponse)
        assert get_result.role.id == target_role.role.id
        assert get_result.role.name == target_role.role.name
        assert get_result.role.description == target_role.role.description

    @pytest.mark.asyncio
    async def test_get_nonexistent_role_returns_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(NotFoundError):
            await admin_registry.rbac.get_role(uuid.uuid4())


class TestRoleSearch:
    @pytest.mark.asyncio
    async def test_admin_searches_roles(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        await role_factory()
        result = await admin_registry.rbac.search_roles(SearchRolesRequest())
        assert isinstance(result, SearchRolesResponse)
        assert result.pagination.total >= 1
        assert len(result.roles) >= 1

    @pytest.mark.asyncio
    async def test_search_with_name_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        marker = f"searchable-{unique}"
        await role_factory(name=marker, description=f"Searchable role {unique}")
        result = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(name=StringFilter(contains=marker)),
            )
        )
        assert result.pagination.total >= 1
        assert any(r.name == marker for r in result.roles)

    @pytest.mark.asyncio
    async def test_search_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.rbac.search_roles(
            SearchRolesRequest(limit=1, offset=0),
        )
        assert result.pagination.limit == 1
        assert len(result.roles) <= 1

    @pytest.mark.asyncio
    async def test_regular_user_cannot_search_roles(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.rbac.search_roles(SearchRolesRequest())


class TestRoleUpdate:
    @pytest.mark.asyncio
    async def test_admin_updates_role_name(
        self,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
    ) -> None:
        unique = secrets.token_hex(4)
        update_result = await admin_registry.rbac.update_role(
            target_role.role.id,
            UpdateRoleRequest(name=f"updated-role-{unique}"),
        )
        assert isinstance(update_result, UpdateRoleResponse)
        assert update_result.role.name == f"updated-role-{unique}"
        assert update_result.role.id == target_role.role.id

    @pytest.mark.asyncio
    async def test_admin_updates_role_description(
        self,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
    ) -> None:
        unique = secrets.token_hex(4)
        update_result = await admin_registry.rbac.update_role(
            target_role.role.id,
            UpdateRoleRequest(description=f"Updated description {unique}"),
        )
        assert isinstance(update_result, UpdateRoleResponse)
        assert update_result.role.description == f"Updated description {unique}"

    @pytest.mark.asyncio
    async def test_regular_user_cannot_update_role(
        self,
        user_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.rbac.update_role(
                target_role.role.id,
                UpdateRoleRequest(description="Denied"),
            )


class TestRoleDelete:
    @pytest.mark.asyncio
    async def test_admin_soft_deletes_role(
        self,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
    ) -> None:
        delete_result = await admin_registry.rbac.delete_role(
            DeleteRoleRequest(role_id=target_role.role.id)
        )
        assert isinstance(delete_result, DeleteRoleResponse)
        assert delete_result.deleted is True

    @pytest.mark.asyncio
    async def test_regular_user_cannot_delete_role(
        self,
        user_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.rbac.delete_role(DeleteRoleRequest(role_id=target_role.role.id))


class TestRolePurge:
    @pytest.mark.asyncio
    async def test_admin_purges_role(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        r = await role_factory()
        purge_result = await admin_registry.rbac.purge_role(PurgeRoleRequest(role_id=r.role.id))
        assert isinstance(purge_result, DeleteRoleResponse)
        assert purge_result.deleted is True
        with pytest.raises(NotFoundError):
            await admin_registry.rbac.get_role(r.role.id)

    @pytest.mark.asyncio
    async def test_regular_user_cannot_purge_role(
        self,
        user_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.rbac.purge_role(PurgeRoleRequest(role_id=target_role.role.id))


class TestRoleAssignment:
    @pytest.mark.asyncio
    async def test_admin_assigns_role_to_user(
        self,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        admin_user_fixture: UserFixtureData,
    ) -> None:
        result = await admin_registry.rbac.assign_role(
            AssignRoleRequest(
                user_id=admin_user_fixture.user_uuid,
                role_id=target_role.role.id,
            )
        )
        assert isinstance(result, AssignRoleResponse)
        assert result.user_id == admin_user_fixture.user_uuid
        assert result.role_id == target_role.role.id

        # Clean up: revoke the assignment
        await admin_registry.rbac.revoke_role(
            RevokeRoleRequest(
                user_id=admin_user_fixture.user_uuid,
                role_id=target_role.role.id,
            )
        )

    @pytest.mark.asyncio
    async def test_admin_revokes_role_from_user(
        self,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        admin_user_fixture: UserFixtureData,
    ) -> None:
        # Assign first
        await admin_registry.rbac.assign_role(
            AssignRoleRequest(
                user_id=admin_user_fixture.user_uuid,
                role_id=target_role.role.id,
            )
        )
        # Revoke
        revoke_result = await admin_registry.rbac.revoke_role(
            RevokeRoleRequest(
                user_id=admin_user_fixture.user_uuid,
                role_id=target_role.role.id,
            )
        )
        assert isinstance(revoke_result, RevokeRoleResponse)
        assert revoke_result.user_id == admin_user_fixture.user_uuid
        assert revoke_result.role_id == target_role.role.id

    @pytest.mark.asyncio
    async def test_admin_searches_assigned_users(
        self,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        admin_user_fixture: UserFixtureData,
    ) -> None:
        # Assign role
        await admin_registry.rbac.assign_role(
            AssignRoleRequest(
                user_id=admin_user_fixture.user_uuid,
                role_id=target_role.role.id,
            )
        )
        # Search assigned users
        result = await admin_registry.rbac.search_assigned_users(
            target_role.role.id,
            SearchUsersAssignedToRoleRequest(),
        )
        assert isinstance(result, SearchUsersAssignedToRoleResponse)
        assert result.pagination.total >= 1
        assert any(u.user_id == admin_user_fixture.user_uuid for u in result.users)

        # Clean up
        await admin_registry.rbac.revoke_role(
            RevokeRoleRequest(
                user_id=admin_user_fixture.user_uuid,
                role_id=target_role.role.id,
            )
        )

    @pytest.mark.asyncio
    async def test_regular_user_cannot_assign_role(
        self,
        user_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.rbac.assign_role(
                AssignRoleRequest(
                    user_id=regular_user_fixture.user_uuid,
                    role_id=target_role.role.id,
                )
            )

    @pytest.mark.asyncio
    async def test_regular_user_cannot_revoke_role(
        self,
        user_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        regular_user_fixture: UserFixtureData,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.rbac.revoke_role(
                RevokeRoleRequest(
                    user_id=regular_user_fixture.user_uuid,
                    role_id=target_role.role.id,
                )
            )


class TestScopeManagement:
    @pytest.mark.asyncio
    async def test_admin_gets_scope_types(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.rbac.get_scope_types()
        assert isinstance(result, GetScopeTypesResponse)
        assert len(result.items) > 0

    @pytest.mark.asyncio
    async def test_admin_searches_scopes(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.rbac.search_scopes("domain", SearchScopesRequest())
        assert isinstance(result, SearchScopesResponse)
        assert result.pagination.total >= 1
        assert len(result.items) >= 1

    @pytest.mark.asyncio
    async def test_regular_user_cannot_get_scope_types(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.rbac.get_scope_types()


class TestEntityManagement:
    @pytest.mark.asyncio
    async def test_admin_gets_entity_types(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.rbac.get_entity_types()
        assert isinstance(result, GetEntityTypesResponse)
        assert len(result.items) > 0

    @pytest.mark.asyncio
    async def test_regular_user_cannot_get_entity_types(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.rbac.get_entity_types()
