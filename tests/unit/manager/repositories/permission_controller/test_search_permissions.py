"""
Tests for PermissionControllerRepository permission search functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest

from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    ScopeType,
)
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.permission_group import PermissionGroupRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.permission_controller.options import (
    ObjectPermissionConditions,
    ObjectPermissionOrders,
    PermissionGroupConditions,
    PermissionGroupOrders,
    ScopedPermissionConditions,
    ScopedPermissionOrders,
)
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.testutils.db import with_tables


@dataclass
class RoleWithPermissionGroups:
    role_id: uuid.UUID
    perm_group_ids: list[uuid.UUID]


@dataclass
class PermissionGroupWithPermissions:
    perm_group_id: uuid.UUID
    permission_ids: list[uuid.UUID]


@dataclass
class RoleWithObjectPermissions:
    role_id: uuid.UUID
    object_permission_ids: list[uuid.UUID]


class TestSearchPermissionGroups:
    """Tests for searching permission groups (scopes of a role)."""

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
                PermissionGroupRow,
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
    async def role_with_permission_groups(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> RoleWithPermissionGroups:
        """Create a role with multiple permission groups."""
        role_id = uuid.uuid4()
        perm_group_ids: list[uuid.UUID] = []

        async with db_with_rbac_tables.begin_session() as db_sess:
            role = RoleRow(
                id=role_id,
                name="test-role",
                description="Test role",
            )
            db_sess.add(role)
            await db_sess.flush()

            for scope_type, scope_id in [
                (ScopeType.DOMAIN, "domain-1"),
                (ScopeType.PROJECT, "project-1"),
                (ScopeType.USER, "user-1"),
            ]:
                perm_group = PermissionGroupRow(
                    role_id=role_id,
                    scope_type=scope_type,
                    scope_id=scope_id,
                )
                db_sess.add(perm_group)
                await db_sess.flush()
                perm_group_ids.append(perm_group.id)

        return RoleWithPermissionGroups(role_id=role_id, perm_group_ids=perm_group_ids)

    async def test_search_permission_groups_with_role_id_filter(
        self,
        repository: PermissionControllerRepository,
        role_with_permission_groups: RoleWithPermissionGroups,
    ) -> None:
        """Filter by role_id should return all permission groups of that role."""
        querier = BatchQuerier(
            conditions=[
                PermissionGroupConditions.by_role_id(role_with_permission_groups.role_id),
            ],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_permission_groups(querier)

        assert result.total_count == len(role_with_permission_groups.perm_group_ids)

    async def test_search_permission_groups_with_scope_type_filter(
        self,
        repository: PermissionControllerRepository,
        role_with_permission_groups: RoleWithPermissionGroups,
    ) -> None:
        querier = BatchQuerier(
            conditions=[
                PermissionGroupConditions.by_role_id(role_with_permission_groups.role_id),
                PermissionGroupConditions.by_scope_type(ScopeType.DOMAIN),
            ],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_permission_groups(querier)

        assert result.total_count == 1
        assert result.items[0].scope_id.scope_type == ScopeType.DOMAIN

    async def test_search_permission_groups_ordered_by_scope_type(
        self,
        repository: PermissionControllerRepository,
        role_with_permission_groups: RoleWithPermissionGroups,
    ) -> None:
        querier = BatchQuerier(
            conditions=[PermissionGroupConditions.by_role_id(role_with_permission_groups.role_id)],
            orders=[PermissionGroupOrders.scope_type(ascending=True)],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_permission_groups(querier)

        scope_types = [item.scope_id.scope_type for item in result.items]
        assert scope_types == sorted(scope_types, key=lambda st: st.value)


class TestSearchScopedPermissions:
    """Tests for searching scoped permissions within a permission group."""

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
                PermissionGroupRow,
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
    async def permission_group_with_permissions(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> PermissionGroupWithPermissions:
        """Create a permission group with multiple permissions."""
        role_id = uuid.uuid4()
        perm_ids: list[uuid.UUID] = []

        async with db_with_rbac_tables.begin_session() as db_sess:
            role = RoleRow(
                id=role_id,
                name="test-role-perms",
                description="Test role for permissions",
            )
            db_sess.add(role)
            await db_sess.flush()

            perm_group = PermissionGroupRow(
                role_id=role_id,
                scope_type=ScopeType.DOMAIN,
                scope_id="test-domain",
            )
            db_sess.add(perm_group)
            await db_sess.flush()
            perm_group_id = perm_group.id

            for entity_type, operation in [
                (EntityType.VFOLDER, OperationType.READ),
                (EntityType.VFOLDER, OperationType.UPDATE),
                (EntityType.SESSION, OperationType.CREATE),
                (EntityType.IMAGE, OperationType.READ),
            ]:
                perm = PermissionRow(
                    permission_group_id=perm_group_id,
                    entity_type=entity_type,
                    operation=operation,
                )
                db_sess.add(perm)
                await db_sess.flush()
                perm_ids.append(perm.id)

        return PermissionGroupWithPermissions(perm_group_id=perm_group_id, permission_ids=perm_ids)

    async def test_search_scoped_permissions_with_entity_type_filter(
        self,
        repository: PermissionControllerRepository,
        permission_group_with_permissions: PermissionGroupWithPermissions,
    ) -> None:
        querier = BatchQuerier(
            conditions=[
                ScopedPermissionConditions.by_permission_group_id(
                    permission_group_with_permissions.perm_group_id
                ),
                ScopedPermissionConditions.by_entity_type(EntityType.VFOLDER),
            ],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_scoped_permissions(querier)

        assert result.total_count == 2
        for item in result.items:
            assert item.entity_type == EntityType.VFOLDER

    async def test_search_scoped_permissions_ordered_by_entity_type(
        self,
        repository: PermissionControllerRepository,
        permission_group_with_permissions: PermissionGroupWithPermissions,
    ) -> None:
        querier = BatchQuerier(
            conditions=[
                ScopedPermissionConditions.by_permission_group_id(
                    permission_group_with_permissions.perm_group_id
                ),
            ],
            orders=[ScopedPermissionOrders.entity_type(ascending=True)],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_scoped_permissions(querier)

        entity_types = [item.entity_type for item in result.items]
        assert entity_types == sorted(entity_types, key=lambda et: et.value)


class TestSearchObjectPermissions:
    """Tests for searching object permissions of a role."""

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
                PermissionGroupRow,
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
    async def role_with_object_permissions(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> RoleWithObjectPermissions:
        """Create a role with object permissions."""
        role_id = uuid.uuid4()
        obj_perm_ids: list[uuid.UUID] = []

        async with db_with_rbac_tables.begin_session() as db_sess:
            role = RoleRow(
                id=role_id,
                name="test-role-obj-perms",
                description="Test role for object permissions",
            )
            db_sess.add(role)
            await db_sess.flush()

            perm_group = PermissionGroupRow(
                role_id=role_id,
                scope_type=ScopeType.PROJECT,
                scope_id="project-1",
            )
            db_sess.add(perm_group)
            await db_sess.flush()
            perm_group_id = perm_group.id

            for entity_type, entity_id, operation in [
                (EntityType.VFOLDER, "folder-1", OperationType.READ),
                (EntityType.VFOLDER, "folder-2", OperationType.UPDATE),
                (EntityType.SESSION, "session-1", OperationType.READ),
            ]:
                op = ObjectPermissionRow(
                    role_id=role_id,
                    permission_group_id=perm_group_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    operation=operation,
                )
                db_sess.add(op)
                await db_sess.flush()
                obj_perm_ids.append(op.id)

        return RoleWithObjectPermissions(role_id=role_id, object_permission_ids=obj_perm_ids)

    async def test_search_object_permissions_with_role_id_filter(
        self,
        repository: PermissionControllerRepository,
        role_with_object_permissions: RoleWithObjectPermissions,
    ) -> None:
        """Filter by role_id should return all object permissions of that role."""
        querier = BatchQuerier(
            conditions=[
                ObjectPermissionConditions.by_role_id(role_with_object_permissions.role_id),
            ],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_object_permissions(querier)

        assert result.total_count == len(role_with_object_permissions.object_permission_ids)

    async def test_search_object_permissions_with_entity_type_filter(
        self,
        repository: PermissionControllerRepository,
        role_with_object_permissions: RoleWithObjectPermissions,
    ) -> None:
        querier = BatchQuerier(
            conditions=[
                ObjectPermissionConditions.by_role_id(role_with_object_permissions.role_id),
                ObjectPermissionConditions.by_entity_type(EntityType.VFOLDER),
            ],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_object_permissions(querier)

        assert result.total_count == 2
        for item in result.items:
            assert item.object_id.entity_type == EntityType.VFOLDER

    async def test_search_object_permissions_ordered_by_entity_type(
        self,
        repository: PermissionControllerRepository,
        role_with_object_permissions: RoleWithObjectPermissions,
    ) -> None:
        querier = BatchQuerier(
            conditions=[
                ObjectPermissionConditions.by_role_id(role_with_object_permissions.role_id)
            ],
            orders=[ObjectPermissionOrders.entity_type(ascending=True)],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_object_permissions(querier)

        entity_types = [item.object_id.entity_type for item in result.items]
        assert entity_types == sorted(entity_types, key=lambda et: et.value)
