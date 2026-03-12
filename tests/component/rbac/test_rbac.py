from __future__ import annotations

import secrets
import uuid
from collections.abc import Callable, Coroutine
from typing import Any

import pytest

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
    RoleOrder,
    SearchEntitiesRequest,
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
    SearchEntitiesResponse,
    SearchRolesResponse,
    SearchScopesResponse,
    SearchUsersAssignedToRoleResponse,
    UpdateRoleResponse,
)
from ai.backend.common.dto.manager.rbac.types import (
    OrderDirection,
    RoleOrderField,
    RoleSource,
    RoleStatus,
)

RoleFactory = Callable[..., Coroutine[Any, Any, CreateRoleResponse]]


class TestRoleCreate:
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

    async def test_get_nonexistent_role_returns_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(NotFoundError):
            await admin_registry.rbac.get_role(uuid.uuid4())


class TestRoleSearch:
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

    async def test_search_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.rbac.search_roles(
            SearchRolesRequest(limit=1, offset=0),
        )
        assert result.pagination.limit == 1
        assert len(result.roles) <= 1

    async def test_search_with_status_filter_active(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        """Search with status filter ACTIVE returns only active roles."""
        unique = secrets.token_hex(4)
        active_role = await role_factory(
            name=f"active-{unique}",
            status=RoleStatus.ACTIVE,
        )

        result = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(
                    name=StringFilter(contains=f"active-{unique}"),
                    statuses=[RoleStatus.ACTIVE],
                ),
            )
        )

        assert result.pagination.total >= 1
        assert all(r.status == RoleStatus.ACTIVE for r in result.roles)
        assert any(r.id == active_role.role.id for r in result.roles)

    async def test_search_with_status_filter_inactive(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        """Search with status filter INACTIVE returns only inactive roles."""
        unique = secrets.token_hex(4)
        inactive_role = await role_factory(
            name=f"inactive-{unique}",
            status=RoleStatus.INACTIVE,
        )

        result = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(
                    name=StringFilter(contains=f"inactive-{unique}"),
                    statuses=[RoleStatus.INACTIVE],
                ),
            )
        )

        assert result.pagination.total >= 1
        assert all(r.status == RoleStatus.INACTIVE for r in result.roles)
        assert any(r.id == inactive_role.role.id for r in result.roles)

    async def test_search_with_pagination_offset(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        """Search with pagination offset skips correct number of items."""
        unique = secrets.token_hex(4)
        # Create 3 roles
        for i in range(3):
            await role_factory(name=f"offset-{unique}-{i}")

        # Get first page
        page1 = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(name=StringFilter(contains=f"offset-{unique}")),
                limit=2,
                offset=0,
            )
        )

        # Get second page
        page2 = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(name=StringFilter(contains=f"offset-{unique}")),
                limit=2,
                offset=2,
            )
        )

        assert page1.pagination.total == 3
        assert len(page1.roles) == 2
        assert page2.pagination.total == 3
        assert len(page2.roles) == 1
        # Ensure different roles on different pages
        page1_ids = {r.id for r in page1.roles}
        page2_ids = {r.id for r in page2.roles}
        assert page1_ids.isdisjoint(page2_ids)

    async def test_search_with_sorting_asc(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        """Search with sorting ascending returns correctly ordered results."""
        unique = secrets.token_hex(4)
        # Create roles with specific names for sorting
        await role_factory(name=f"sort-{unique}-z-last")
        await role_factory(name=f"sort-{unique}-a-first")
        await role_factory(name=f"sort-{unique}-m-middle")

        result = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(name=StringFilter(contains=f"sort-{unique}")),
                order=[RoleOrder(field=RoleOrderField.NAME, direction=OrderDirection.ASC)],
            )
        )

        assert len(result.roles) == 3
        names = [r.name for r in result.roles]
        assert names == sorted(names)
        assert names[0].endswith("a-first")
        assert names[2].endswith("z-last")

    async def test_search_with_sorting_desc(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        """Search with sorting descending returns correctly ordered results."""
        unique = secrets.token_hex(4)
        # Create roles with specific names for sorting
        await role_factory(name=f"desc-{unique}-a-first")
        await role_factory(name=f"desc-{unique}-z-last")
        await role_factory(name=f"desc-{unique}-m-middle")

        result = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(name=StringFilter(contains=f"desc-{unique}")),
                order=[RoleOrder(field=RoleOrderField.NAME, direction=OrderDirection.DESC)],
            )
        )

        assert len(result.roles) == 3
        names = [r.name for r in result.roles]
        assert names == sorted(names, reverse=True)
        assert names[0].endswith("z-last")
        assert names[2].endswith("a-first")

    async def test_search_empty_result(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Search with non-matching filter returns empty result."""
        unique = secrets.token_hex(4)
        nonexistent_marker = f"this-role-definitely-does-not-exist-{unique}"

        result = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(name=StringFilter(contains=nonexistent_marker)),
            )
        )

        assert isinstance(result, SearchRolesResponse)
        assert result.pagination.total == 0
        assert len(result.roles) == 0

    async def test_search_with_source_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        """Search with source filter returns only roles from specified source."""
        unique = secrets.token_hex(4)
        custom_role = await role_factory(
            name=f"custom-{unique}",
            source=RoleSource.CUSTOM,
        )

        result = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(
                    name=StringFilter(contains=f"custom-{unique}"),
                    sources=[RoleSource.CUSTOM],
                ),
            )
        )

        assert result.pagination.total >= 1
        assert all(r.source == RoleSource.CUSTOM for r in result.roles)
        assert any(r.id == custom_role.role.id for r in result.roles)

    async def test_regular_user_cannot_search_roles(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.rbac.search_roles(SearchRolesRequest())


class TestRoleUpdate:
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

    async def test_regular_user_cannot_delete_role(
        self,
        user_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.rbac.delete_role(DeleteRoleRequest(role_id=target_role.role.id))


class TestRolePurge:
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

    async def test_regular_user_cannot_purge_role(
        self,
        user_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.rbac.purge_role(PurgeRoleRequest(role_id=target_role.role.id))


class TestRoleAssignment:
    async def test_admin_assigns_role_to_user(
        self,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        admin_user_fixture: Any,
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

    async def test_admin_revokes_role_from_user(
        self,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        admin_user_fixture: Any,
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

    async def test_admin_searches_assigned_users(
        self,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        admin_user_fixture: Any,
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

    async def test_regular_user_cannot_assign_role(
        self,
        user_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        regular_user_fixture: Any,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.rbac.assign_role(
                AssignRoleRequest(
                    user_id=regular_user_fixture.user_uuid,
                    role_id=target_role.role.id,
                )
            )

    async def test_regular_user_cannot_revoke_role(
        self,
        user_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        regular_user_fixture: Any,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.rbac.revoke_role(
                RevokeRoleRequest(
                    user_id=regular_user_fixture.user_uuid,
                    role_id=target_role.role.id,
                )
            )


class TestScopeManagement:
    async def test_admin_gets_scope_types(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.rbac.get_scope_types()
        assert isinstance(result, GetScopeTypesResponse)
        assert len(result.items) > 0

    async def test_admin_searches_scopes(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.rbac.search_scopes("domain", SearchScopesRequest())
        assert isinstance(result, SearchScopesResponse)
        assert result.pagination.total >= 1
        assert len(result.items) >= 1

    async def test_search_scopes_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        """Search scopes with pagination returns correct page."""
        result = await admin_registry.rbac.search_scopes(
            "domain",
            SearchScopesRequest(limit=1, offset=0),
        )

        assert isinstance(result, SearchScopesResponse)
        assert result.pagination.limit == 1
        assert len(result.items) <= 1

    async def test_regular_user_cannot_get_scope_types(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.rbac.get_scope_types()

    async def test_regular_user_cannot_search_scopes(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        """Regular user cannot search scopes (admin-only operation)."""
        with pytest.raises(PermissionDeniedError):
            await user_registry.rbac.search_scopes("domain", SearchScopesRequest())


class TestEntityManagement:
    async def test_admin_gets_entity_types(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.rbac.get_entity_types()
        assert isinstance(result, GetEntityTypesResponse)
        assert len(result.items) > 0

    async def test_search_entities_in_domain(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
    ) -> None:
        """Search entities within a domain scope."""
        # Search for users in the test domain
        result = await admin_registry.rbac.search_entities(
            scope_type="domain",
            scope_id=domain_fixture,
            entity_type="user",
            request=SearchEntitiesRequest(),
        )

        assert isinstance(result, SearchEntitiesResponse)
        # Test domain may be empty, just verify search works
        assert result.pagination.total >= len(result.items)
        assert isinstance(result.items, list)

    async def test_search_entities_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
        domain_fixture: str,
    ) -> None:
        """Search entities with pagination returns correct page."""
        result = await admin_registry.rbac.search_entities(
            scope_type="domain",
            scope_id=domain_fixture,
            entity_type="user",
            request=SearchEntitiesRequest(limit=1, offset=0),
        )

        assert isinstance(result, SearchEntitiesResponse)
        assert result.pagination.limit == 1
        assert len(result.items) <= 1

    async def test_regular_user_cannot_get_entity_types(
        self,
        user_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.rbac.get_entity_types()

    async def test_regular_user_cannot_search_entities(
        self,
        user_registry: BackendAIClientRegistry,
        domain_fixture: str,
    ) -> None:
        """Regular user cannot search entities."""
        # Entity search should be admin-only
        with pytest.raises(PermissionDeniedError):
            await user_registry.rbac.search_entities(
                scope_type="domain",
                scope_id=domain_fixture,
                entity_type="user",
                request=SearchEntitiesRequest(),
            )
