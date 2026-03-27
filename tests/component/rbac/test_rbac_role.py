from __future__ import annotations

import secrets
from typing import Any

import pytest

from ai.backend.client.v2.exceptions import ConflictError, NotFoundError, PermissionDeniedError
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
    SearchRolesRequest,
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
from ai.backend.common.dto.manager.rbac.types import (
    OrderDirection,
    RoleOrderField,
    RoleSource,
    RoleStatus,
)

from .conftest import RoleFactory


class TestRoleCRUD:
    """Role CRUD lifecycle: create → get → update → soft-delete → purge."""

    async def test_create_role_returns_custom_source(
        self,
        role_factory: RoleFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        result = await role_factory(
            name=f"crud-create-{unique}",
            description=f"CRUD test role {unique}",
        )
        assert isinstance(result, CreateRoleResponse)
        assert result.role.name == f"crud-create-{unique}"
        assert result.role.description == f"CRUD test role {unique}"
        assert result.role.source == RoleSource.CUSTOM
        assert result.role.status == RoleStatus.ACTIVE
        assert result.role.created_at is not None
        assert result.role.updated_at is not None
        assert result.role.deleted_at is None

    async def test_get_role_by_id(
        self,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
    ) -> None:
        get_result = await admin_registry.rbac.get_role(target_role.role.id)
        assert isinstance(get_result, GetRoleResponse)
        assert get_result.role.id == target_role.role.id
        assert get_result.role.name == target_role.role.name
        assert get_result.role.description == target_role.role.description
        assert get_result.role.source == RoleSource.CUSTOM
        assert get_result.role.status == RoleStatus.ACTIVE

    async def test_update_role_name_and_description(
        self,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
    ) -> None:
        unique = secrets.token_hex(4)
        new_name = f"updated-name-{unique}"
        new_desc = f"Updated description {unique}"

        update_result = await admin_registry.rbac.update_role(
            target_role.role.id,
            UpdateRoleRequest(name=new_name, description=new_desc),
        )
        assert isinstance(update_result, UpdateRoleResponse)
        assert update_result.role.name == new_name
        assert update_result.role.description == new_desc
        assert update_result.role.id == target_role.role.id

        # Verify via get
        fetched = await admin_registry.rbac.get_role(target_role.role.id)
        assert fetched.role.name == new_name
        assert fetched.role.description == new_desc

    async def test_soft_delete_excludes_from_active_search(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        marker = f"soft-del-crud-{unique}"
        created = await role_factory(name=marker)
        role_id = created.role.id

        # Confirm visible in ACTIVE search
        before = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(
                    name=StringFilter(contains=marker),
                    statuses=[RoleStatus.ACTIVE],
                ),
            )
        )
        assert any(r.id == role_id for r in before.roles)

        # Soft delete
        delete_result = await admin_registry.rbac.delete_role(DeleteRoleRequest(role_id=role_id))
        assert isinstance(delete_result, DeleteRoleResponse)
        assert delete_result.deleted is True

        # Excluded from ACTIVE search
        after_active = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(
                    name=StringFilter(contains=marker),
                    statuses=[RoleStatus.ACTIVE],
                ),
            )
        )
        assert not any(r.id == role_id for r in after_active.roles)

    async def test_soft_deleted_role_included_in_deleted_search(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        marker = f"del-search-{unique}"
        created = await role_factory(name=marker)
        role_id = created.role.id

        # Soft delete
        await admin_registry.rbac.delete_role(DeleteRoleRequest(role_id=role_id))

        # Included in DELETED search
        deleted_search = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(
                    name=StringFilter(contains=marker),
                    statuses=[RoleStatus.DELETED],
                ),
            )
        )
        assert isinstance(deleted_search, SearchRolesResponse)
        assert any(r.id == role_id for r in deleted_search.roles)
        matching = next(r for r in deleted_search.roles if r.id == role_id)
        assert matching.status == RoleStatus.DELETED

    async def test_purge_makes_role_unretrievable(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        created = await role_factory()
        role_id = created.role.id

        # Verify retrievable before purge
        get_result = await admin_registry.rbac.get_role(role_id)
        assert get_result.role.id == role_id

        # Purge
        purge_result = await admin_registry.rbac.purge_role(PurgeRoleRequest(role_id=role_id))
        assert isinstance(purge_result, DeleteRoleResponse)
        assert purge_result.deleted is True

        # 404 after purge
        with pytest.raises(NotFoundError):
            await admin_registry.rbac.get_role(role_id)


class TestRoleSearch:
    """Search roles with status filters, name filtering, ordering, and pagination."""

    async def test_search_active_roles_excludes_deleted(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        prefix = f"search-active-{unique}"
        active_role = await role_factory(name=f"{prefix}-a")
        deleted_role = await role_factory(name=f"{prefix}-d")

        # Soft-delete one
        await admin_registry.rbac.delete_role(DeleteRoleRequest(role_id=deleted_role.role.id))

        result = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(
                    name=StringFilter(contains=prefix),
                    statuses=[RoleStatus.ACTIVE],
                ),
            )
        )
        assert isinstance(result, SearchRolesResponse)
        role_ids = [r.id for r in result.roles]
        assert active_role.role.id in role_ids
        assert deleted_role.role.id not in role_ids

    async def test_search_deleted_roles_excludes_active(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        prefix = f"search-deleted-{unique}"
        active_role = await role_factory(name=f"{prefix}-a")
        deleted_role = await role_factory(name=f"{prefix}-d")

        await admin_registry.rbac.delete_role(DeleteRoleRequest(role_id=deleted_role.role.id))

        result = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(
                    name=StringFilter(contains=prefix),
                    statuses=[RoleStatus.DELETED],
                ),
            )
        )
        role_ids = [r.id for r in result.roles]
        assert deleted_role.role.id in role_ids
        assert active_role.role.id not in role_ids
        assert all(r.status == RoleStatus.DELETED for r in result.roles)

    async def test_search_by_name_filter(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        marker = f"namefilter-{unique}"
        created = await role_factory(name=marker)

        result = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(name=StringFilter(contains=marker)),
            )
        )
        assert len(result.roles) == 1
        assert any(r.id == created.role.id for r in result.roles)
        assert all(marker in r.name for r in result.roles)

    async def test_search_pagination_limit_offset(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        prefix = f"page-{unique}"
        roles = []
        for i in range(3):
            r = await role_factory(name=f"{prefix}-{i:02d}")
            roles.append(r)

        # Fetch first page (limit=2)
        page1 = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(name=StringFilter(contains=prefix)),
                order=[RoleOrder(field=RoleOrderField.NAME, direction=OrderDirection.ASC)],
                limit=2,
                offset=0,
            )
        )
        assert len(page1.roles) == 2
        assert page1.pagination.total == 3
        assert page1.pagination.offset == 0
        assert page1.pagination.limit == 2

        # Fetch second page (offset=2)
        page2 = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(name=StringFilter(contains=prefix)),
                order=[RoleOrder(field=RoleOrderField.NAME, direction=OrderDirection.ASC)],
                limit=2,
                offset=2,
            )
        )
        assert len(page2.roles) == 1
        assert page2.pagination.offset == 2

        # No overlap between pages
        page1_ids = {r.id for r in page1.roles}
        page2_ids = {r.id for r in page2.roles}
        assert page1_ids.isdisjoint(page2_ids)

    async def test_search_returns_pagination_info(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        marker = f"paginfo-{unique}"
        await role_factory(name=marker)

        result = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(name=StringFilter(contains=marker)),
            )
        )
        assert result.pagination.total == 1
        assert result.pagination.offset == 0

    async def test_search_with_ordering(
        self,
        admin_registry: BackendAIClientRegistry,
        role_factory: RoleFactory,
    ) -> None:
        unique = secrets.token_hex(4)
        prefix = f"order-{unique}"
        await role_factory(name=f"{prefix}-b")
        await role_factory(name=f"{prefix}-a")
        await role_factory(name=f"{prefix}-c")

        asc_result = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(name=StringFilter(contains=prefix)),
                order=[RoleOrder(field=RoleOrderField.NAME, direction=OrderDirection.ASC)],
            )
        )
        names_asc = [r.name for r in asc_result.roles]
        assert names_asc == sorted(names_asc)

        desc_result = await admin_registry.rbac.search_roles(
            SearchRolesRequest(
                filter=RoleFilter(name=StringFilter(contains=prefix)),
                order=[RoleOrder(field=RoleOrderField.NAME, direction=OrderDirection.DESC)],
            )
        )
        names_desc = [r.name for r in desc_result.roles]
        assert names_desc == sorted(names_desc, reverse=True)


class TestRoleAssignment:
    """Role assignment: assign, revoke, search assigned users, duplicate detection."""

    async def test_assign_role_to_user(
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

        # Clean up
        await admin_registry.rbac.revoke_role(
            RevokeRoleRequest(
                user_id=admin_user_fixture.user_uuid,
                role_id=target_role.role.id,
            )
        )

    async def test_revoke_role_from_user(
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

        # Verify user no longer in assigned list
        search_result = await admin_registry.rbac.search_assigned_users(
            target_role.role.id,
            SearchUsersAssignedToRoleRequest(),
        )
        assert not any(u.user_id == admin_user_fixture.user_uuid for u in search_result.users)

    async def test_search_assigned_users(
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
        assert result.pagination.total == 1
        assert any(u.user_id == admin_user_fixture.user_uuid for u in result.users)

        # Verify assigned user has granted_at
        assigned = next(u for u in result.users if u.user_id == admin_user_fixture.user_uuid)
        assert assigned.granted_at is not None

        # Clean up
        await admin_registry.rbac.revoke_role(
            RevokeRoleRequest(
                user_id=admin_user_fixture.user_uuid,
                role_id=target_role.role.id,
            )
        )

    async def test_duplicate_assignment_raises_conflict(
        self,
        admin_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
        admin_user_fixture: Any,
    ) -> None:
        # First assignment
        await admin_registry.rbac.assign_role(
            AssignRoleRequest(
                user_id=admin_user_fixture.user_uuid,
                role_id=target_role.role.id,
            )
        )

        # Duplicate assignment should raise ConflictError
        with pytest.raises(ConflictError):
            await admin_registry.rbac.assign_role(
                AssignRoleRequest(
                    user_id=admin_user_fixture.user_uuid,
                    role_id=target_role.role.id,
                )
            )

        # Clean up
        await admin_registry.rbac.revoke_role(
            RevokeRoleRequest(
                user_id=admin_user_fixture.user_uuid,
                role_id=target_role.role.id,
            )
        )


class TestRolePermissions:
    """Regular (non-admin) user cannot manage roles: create, delete, assign → 403."""

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

    async def test_regular_user_cannot_delete_role(
        self,
        user_registry: BackendAIClientRegistry,
        target_role: CreateRoleResponse,
    ) -> None:
        with pytest.raises(PermissionDeniedError):
            await user_registry.rbac.delete_role(DeleteRoleRequest(role_id=target_role.role.id))

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
