from __future__ import annotations

import secrets
import uuid
from typing import Any

import pytest

from ai.backend.client.v2.exceptions import NotFoundError
from ai.backend.client.v2.registry import BackendAIClientRegistry
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.rbac.request import (
    AssignRoleRequest,
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
    GetRoleResponse,
    RevokeRoleResponse,
    SearchRolesResponse,
    SearchUsersAssignedToRoleResponse,
    UpdateRoleResponse,
)
from ai.backend.common.dto.manager.rbac.types import RoleStatus

from .conftest import RoleFactory


class TestRBACRoleLifecycle:
    """Full RBAC role lifecycle: create -> assign -> verify -> revoke -> verify -> delete."""

    async def test_full_role_lifecycle(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
        admin_user_fixture: Any,
    ) -> None:
        unique = secrets.token_hex(4)
        role_name = f"lifecycle-role-{unique}"

        # 1. Create role
        created = await role_factory(name=role_name, description="Lifecycle test role")
        assert isinstance(created, CreateRoleResponse)
        role_id = created.role.id

        # 2. Assign role to user
        assign_result = await admin_registry.rbac.assign_role(
            AssignRoleRequest(
                user_id=admin_user_fixture.user_uuid,
                role_id=role_id,
            )
        )
        assert isinstance(assign_result, AssignRoleResponse)
        assert assign_result.role_id == role_id
        assert assign_result.user_id == admin_user_fixture.user_uuid

        # 3. Verify assignment via search_assigned_users
        search_result = await admin_registry.rbac.search_assigned_users(
            role_id,
            SearchUsersAssignedToRoleRequest(),
        )
        assert isinstance(search_result, SearchUsersAssignedToRoleResponse)
        assert search_result.pagination.total >= 1
        assigned_user_ids = [u.user_id for u in search_result.users]
        assert admin_user_fixture.user_uuid in assigned_user_ids

        # 4. Revoke role
        revoke_result = await admin_registry.rbac.revoke_role(
            RevokeRoleRequest(
                user_id=admin_user_fixture.user_uuid,
                role_id=role_id,
            )
        )
        assert isinstance(revoke_result, RevokeRoleResponse)
        assert revoke_result.role_id == role_id

        # 5. Verify revocation — user no longer assigned
        search_after = await admin_registry.rbac.search_assigned_users(
            role_id,
            SearchUsersAssignedToRoleRequest(),
        )
        assigned_after = [u.user_id for u in search_after.users]
        assert admin_user_fixture.user_uuid not in assigned_after

        # 6. Soft delete role
        delete_result = await admin_registry.rbac.delete_role(DeleteRoleRequest(role_id=role_id))
        assert isinstance(delete_result, DeleteRoleResponse)
        assert delete_result.deleted is True

    async def test_create_update_purge_lifecycle(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        unique = secrets.token_hex(4)

        # Create
        created = await role_factory(
            name=f"update-purge-{unique}",
            description="Will be updated then purged",
        )
        role_id = created.role.id

        # Update
        updated = await admin_registry.rbac.update_role(
            role_id,
            UpdateRoleRequest(
                name=f"updated-{unique}",
                description="Updated description",
            ),
        )
        assert isinstance(updated, UpdateRoleResponse)
        assert updated.role.name == f"updated-{unique}"
        assert updated.role.description == "Updated description"

        # Verify via get
        fetched = await admin_registry.rbac.get_role(role_id)
        assert isinstance(fetched, GetRoleResponse)
        assert fetched.role.name == f"updated-{unique}"

        # Purge (hard delete)
        purge_result = await admin_registry.rbac.purge_role(PurgeRoleRequest(role_id=role_id))
        assert isinstance(purge_result, DeleteRoleResponse)
        assert purge_result.deleted is True

        # Verify gone
        with pytest.raises(NotFoundError):
            await admin_registry.rbac.get_role(role_id)

    async def test_soft_deleted_role_excluded_from_search(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        marker = f"soft-del-{unique}"

        created = await role_factory(name=marker)
        role_id = created.role.id

        # Confirm it appears in search
        before = await admin_registry.rbac.search_roles(
            SearchRolesRequest(filter=RoleFilter(name=StringFilter(contains=marker)))
        )
        assert any(r.id == role_id for r in before.roles)

        # Soft delete
        await admin_registry.rbac.delete_role(DeleteRoleRequest(role_id=role_id))

        # Confirm it no longer appears
        after = await admin_registry.rbac.search_roles(
            SearchRolesRequest(filter=RoleFilter(name=StringFilter(contains=marker)))
        )
        assert not any(r.id == role_id for r in after.roles)


class TestRoleAssignmentAudit:
    """Role assignment audit trail: granted_by and granted_at tracking."""

    async def test_granted_by_recorded_on_assignment(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
        admin_user_fixture: Any,
    ) -> None:
        created = await role_factory()
        role_id = created.role.id

        await admin_registry.rbac.assign_role(
            AssignRoleRequest(
                user_id=admin_user_fixture.user_uuid,
                role_id=role_id,
            )
        )

        result = await admin_registry.rbac.search_assigned_users(
            role_id,
            SearchUsersAssignedToRoleRequest(),
        )
        assert result.pagination.total >= 1
        user_entry = next(u for u in result.users if u.user_id == admin_user_fixture.user_uuid)
        assert user_entry.granted_at is not None

        # Cleanup
        await admin_registry.rbac.revoke_role(
            RevokeRoleRequest(
                user_id=admin_user_fixture.user_uuid,
                role_id=role_id,
            )
        )

    async def test_multiple_roles_assigned_to_same_user(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
        admin_user_fixture: Any,
    ) -> None:
        role_a = await role_factory(name=f"multi-a-{secrets.token_hex(4)}")
        role_b = await role_factory(name=f"multi-b-{secrets.token_hex(4)}")

        await admin_registry.rbac.assign_role(
            AssignRoleRequest(
                user_id=admin_user_fixture.user_uuid,
                role_id=role_a.role.id,
            )
        )
        await admin_registry.rbac.assign_role(
            AssignRoleRequest(
                user_id=admin_user_fixture.user_uuid,
                role_id=role_b.role.id,
            )
        )

        # Verify both assignments exist
        result_a = await admin_registry.rbac.search_assigned_users(
            role_a.role.id, SearchUsersAssignedToRoleRequest()
        )
        result_b = await admin_registry.rbac.search_assigned_users(
            role_b.role.id, SearchUsersAssignedToRoleRequest()
        )
        assert any(u.user_id == admin_user_fixture.user_uuid for u in result_a.users)
        assert any(u.user_id == admin_user_fixture.user_uuid for u in result_b.users)

        # Cleanup
        await admin_registry.rbac.revoke_role(
            RevokeRoleRequest(
                user_id=admin_user_fixture.user_uuid,
                role_id=role_a.role.id,
            )
        )
        await admin_registry.rbac.revoke_role(
            RevokeRoleRequest(
                user_id=admin_user_fixture.user_uuid,
                role_id=role_b.role.id,
            )
        )


class TestScopeAndEntityDiscovery:
    """Scope types and entity types discovery via RBAC API."""

    async def test_scope_types_available(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.rbac.get_scope_types()
        assert len(result.items) > 0
        scope_names = [s.value if hasattr(s, "value") else str(s) for s in result.items]
        assert any("domain" in name.lower() for name in scope_names)

    async def test_entity_types_available(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.rbac.get_entity_types()
        assert len(result.items) > 0

    async def test_search_domain_scopes(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        result = await admin_registry.rbac.search_scopes("domain", SearchScopesRequest())
        assert result.pagination.total >= 1
        assert len(result.items) >= 1


class TestRoleSearchPagination:
    """Search and pagination behavior for roles."""

    async def test_search_with_pagination(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        for i in range(3):
            await role_factory(name=f"page-test-{unique}-{i}")

        # Fetch page 1
        page1 = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(name=StringFilter(contains=f"page-test-{unique}")),
                limit=2,
                offset=0,
            )
        )
        assert isinstance(page1, SearchRolesResponse)
        assert len(page1.roles) == 2
        assert page1.pagination.total == 3

        # Fetch page 2
        page2 = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(name=StringFilter(contains=f"page-test-{unique}")),
                limit=2,
                offset=2,
            )
        )
        assert len(page2.roles) == 1

    async def test_search_with_status_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        await role_factory(name=f"status-{unique}")

        result = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(
                    name=StringFilter(contains=f"status-{unique}"),
                    statuses=[RoleStatus.ACTIVE],
                ),
            )
        )
        assert result.pagination.total >= 1
        assert all(r.status == RoleStatus.ACTIVE for r in result.roles)

    async def test_revoke_nonexistent_assignment_raises_error(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        created = await role_factory()
        with pytest.raises(Exception):
            await admin_registry.rbac.revoke_role(
                RevokeRoleRequest(
                    user_id=uuid.uuid4(),
                    role_id=created.role.id,
                )
            )

    async def test_get_nonexistent_role_raises_not_found(
        self,
        admin_registry: BackendAIClientRegistry,
    ) -> None:
        with pytest.raises(NotFoundError):
            await admin_registry.rbac.get_role(uuid.uuid4())
