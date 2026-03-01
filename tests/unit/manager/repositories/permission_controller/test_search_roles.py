"""
Tests for PermissionControllerRepository.search_roles() functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest

from ai.backend.common.data.filter_specs import StringMatchSpec
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.permission_controller.options import (
    RoleConditions,
    RoleOrders,
)
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.repositories.permission_controller.types import RoleSearchScope
from ai.backend.testutils.db import with_tables


@dataclass
class CreatedRole:
    role_id: uuid.UUID
    role_name: str
    created_at: datetime


class TestSearchRoles:
    """Tests for searching roles with filtering and ordering."""

    @pytest.fixture
    async def db_with_rbac_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                RoleRow,
                UserRoleRow,
                PermissionRow,
                ObjectPermissionRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> PermissionControllerRepository:
        return PermissionControllerRepository(db_with_rbac_tables)

    @pytest.fixture
    async def created_roles(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> list[CreatedRole]:
        """Create multiple roles for testing."""
        created: list[CreatedRole] = []
        base_time = datetime(2026, 1, 1, tzinfo=UTC)

        async with db_with_rbac_tables.begin_session() as db_sess:
            for i, (name, description) in enumerate([
                ("admin-role", "Admin role"),
                ("editor-role", "Editor role"),
                ("viewer-role", "Viewer role"),
            ]):
                created_at = base_time + timedelta(minutes=i)
                role = RoleRow(
                    name=name,
                    description=description,
                    created_at=created_at,
                )
                db_sess.add(role)
                await db_sess.flush()
                created.append(
                    CreatedRole(
                        role_id=role.id,
                        role_name=name,
                        created_at=role.created_at,
                    )
                )

        return created

    async def test_search_roles_with_name_filter(
        self,
        repository: PermissionControllerRepository,
        created_roles: list[CreatedRole],
    ) -> None:
        """Name ends-with filter should match all roles ending with '-role'."""
        querier = BatchQuerier(
            conditions=[
                RoleConditions.by_name_ends_with(
                    StringMatchSpec(value="-role", case_insensitive=False, negated=False)
                ),
            ],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_roles(querier)

        assert result.total_count == len(created_roles)

    async def test_search_roles_ordered_by_name(
        self,
        repository: PermissionControllerRepository,
        created_roles: list[CreatedRole],
    ) -> None:
        querier = BatchQuerier(
            conditions=[],
            orders=[RoleOrders.name(ascending=True)],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_roles(querier)

        names = [item.name for item in result.items]
        expected_names = sorted([r.role_name for r in created_roles])
        assert names == expected_names

    async def test_search_roles_ordered_by_created_at(
        self,
        repository: PermissionControllerRepository,
        created_roles: list[CreatedRole],
    ) -> None:
        """Roles created sequentially should be ordered by created_at."""
        querier = BatchQuerier(
            conditions=[],
            orders=[RoleOrders.created_at(ascending=True)],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_roles(querier)

        role_ids = [item.id for item in result.items]
        expected_role_ids = [r.role_id for r in sorted(created_roles, key=lambda r: r.created_at)]
        assert role_ids == expected_role_ids, (
            f"Failed to order roles by created_at: got {[r.created_at for r in result.items]}, expected {[r.created_at for r in created_roles]}"
        )


class TestSearchRolesWithRBACScope:
    """Tests for RBAC visibility scoping in search_roles()."""

    @pytest.fixture
    async def db_with_rbac_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                RoleRow,
                UserRoleRow,
                PermissionRow,
                ObjectPermissionRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> PermissionControllerRepository:
        return PermissionControllerRepository(db_with_rbac_tables)

    @pytest.fixture
    async def roles_and_users(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> dict[str, uuid.UUID]:
        """Create roles and user assignments for RBAC testing.

        Creates:
        - 3 roles: admin-role, editor-role, viewer-role
        - 2 users: user_a (assigned admin-role), user_b (assigned editor-role)
        - viewer-role is not assigned to anyone
        """
        ids: dict[str, uuid.UUID] = {}
        user_a_id = uuid.uuid4()
        user_b_id = uuid.uuid4()
        ids["user_a"] = user_a_id
        ids["user_b"] = user_b_id

        async with db_with_rbac_tables.begin_session() as db_sess:
            for name in ("admin-role", "editor-role", "viewer-role"):
                role = RoleRow(name=name, description=f"{name} desc")
                db_sess.add(role)
                await db_sess.flush()
                ids[name] = role.id

            # user_a has admin-role via user_roles
            db_sess.add(
                UserRoleRow(
                    user_id=user_a_id,
                    role_id=ids["admin-role"],
                )
            )

            # user_b has editor-role via user_roles
            db_sess.add(
                UserRoleRow(
                    user_id=user_b_id,
                    role_id=ids["editor-role"],
                )
            )

        return ids

    async def test_admin_sees_all_roles_without_scope(
        self,
        repository: PermissionControllerRepository,
        roles_and_users: dict[str, uuid.UUID],
    ) -> None:
        """Without scope (admin), all roles should be returned."""
        querier = BatchQuerier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_roles(querier, scope=None)

        assert result.total_count == 3

    async def test_user_sees_only_assigned_roles(
        self,
        repository: PermissionControllerRepository,
        roles_and_users: dict[str, uuid.UUID],
    ) -> None:
        """User with user_roles assignment sees only their assigned roles."""
        querier = BatchQuerier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )
        scope = RoleSearchScope(user_id=roles_and_users["user_a"])

        result = await repository.search_roles(querier, scope=scope)

        assert result.total_count == 1
        assert result.items[0].id == roles_and_users["admin-role"]

    async def test_another_user_sees_their_assigned_roles(
        self,
        repository: PermissionControllerRepository,
        roles_and_users: dict[str, uuid.UUID],
    ) -> None:
        """Another user sees their own assigned roles."""
        querier = BatchQuerier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )
        scope = RoleSearchScope(user_id=roles_and_users["user_b"])

        result = await repository.search_roles(querier, scope=scope)

        assert result.total_count == 1
        assert result.items[0].id == roles_and_users["editor-role"]

    async def test_user_with_no_assignments_sees_no_roles(
        self,
        repository: PermissionControllerRepository,
        roles_and_users: dict[str, uuid.UUID],
    ) -> None:
        """User with no role assignments sees no roles."""
        querier = BatchQuerier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )
        unassigned_user_id = uuid.uuid4()
        scope = RoleSearchScope(user_id=unassigned_user_id)

        result = await repository.search_roles(querier, scope=scope)

        assert result.total_count == 0
        assert result.items == []

    async def test_user_with_multiple_roles_sees_all(
        self,
        repository: PermissionControllerRepository,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        roles_and_users: dict[str, uuid.UUID],
    ) -> None:
        """User with multiple role assignments sees all their roles."""
        user_id = roles_and_users["user_a"]

        # Also assign viewer-role to user_a
        async with db_with_rbac_tables.begin_session() as db_sess:
            db_sess.add(
                UserRoleRow(
                    user_id=user_id,
                    role_id=roles_and_users["viewer-role"],
                )
            )

        querier = BatchQuerier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )
        scope = RoleSearchScope(user_id=user_id)
        result = await repository.search_roles(querier, scope=scope)

        assert result.total_count == 2
        result_ids = {item.id for item in result.items}
        assert result_ids == {roles_and_users["admin-role"], roles_and_users["viewer-role"]}
