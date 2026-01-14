"""Tests for RBAC foreign key constraints and CASCADE DELETE behavior.

These tests verify that:
1. Deleting a PermissionGroup cascades to ObjectPermission
2. Deleting a PermissionGroup cascades to Permission
3. Role deletion does NOT cascade to PermissionGroup (no FK)
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import sqlalchemy as sa

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
from ai.backend.testutils.db import with_tables


class TestRBACFKConstraints:
    """Test cases for RBAC FK constraints and CASCADE DELETE behavior."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database connection with RBAC tables. TRUNCATE CASCADE handles cleanup."""
        async with with_tables(
            database_connection,
            [
                # FK dependency order: parents before children
                RoleRow,
                UserRoleRow,
                PermissionGroupRow,
                PermissionRow,
                ObjectPermissionRow,
            ],
        ):
            yield database_connection

    @pytest.mark.asyncio
    async def test_cascade_delete_permission_group_removes_object_permissions(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """When a permission_group is deleted, its object_permissions should be CASCADE deleted."""
        db = db_with_cleanup

        role_id = uuid4()
        async with db.begin_session() as db_session:
            role = RoleRow(
                id=role_id,
                name="test-role",
                description="Test role for object permission FK constraint test",
            )
            db_session.add(role)
            await db_session.flush()

            pg = PermissionGroupRow(
                role_id=role_id,
                scope_type=ScopeType.PROJECT,
                scope_id="test-project-id",
            )
            db_session.add(pg)
            await db_session.flush()
            pg_id = pg.id

            op = ObjectPermissionRow(
                role_id=role_id,
                permission_group_id=pg_id,
                entity_type=EntityType.VFOLDER,
                entity_id="test-vfolder-id",
                operation=OperationType.READ,
            )
            db_session.add(op)
            await db_session.flush()
            op_id = op.id

        async with db.begin_session() as db_session:
            result = await db_session.execute(
                sa.select(ObjectPermissionRow).where(ObjectPermissionRow.id == op_id)
            )
            assert result.scalar_one_or_none() is not None

        async with db.begin_session() as db_session:
            result = await db_session.execute(
                sa.select(PermissionGroupRow).where(PermissionGroupRow.id == pg_id)
            )
            pg_to_delete = result.scalar_one()
            await db_session.delete(pg_to_delete)

        async with db.begin_session() as db_session:
            result = await db_session.execute(
                sa.select(ObjectPermissionRow).where(ObjectPermissionRow.id == op_id)
            )
            assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_cascade_delete_permission_group_removes_permissions(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """When a permission_group is deleted, its permissions should be CASCADE deleted."""
        db = db_with_cleanup

        role_id = uuid4()
        async with db.begin_session() as db_session:
            role = RoleRow(
                id=role_id,
                name="test-role-2",
                description="Test role for permission FK constraint test",
            )
            db_session.add(role)
            await db_session.flush()

            pg = PermissionGroupRow(
                role_id=role_id,
                scope_type=ScopeType.DOMAIN,
                scope_id="test-domain-id",
            )
            db_session.add(pg)
            await db_session.flush()
            pg_id = pg.id

            perm = PermissionRow(
                permission_group_id=pg_id,
                entity_type=EntityType.SESSION,
                operation=OperationType.CREATE,
            )
            db_session.add(perm)
            await db_session.flush()
            perm_id = perm.id

        async with db.begin_session() as db_session:
            result = await db_session.execute(
                sa.select(PermissionRow).where(PermissionRow.id == perm_id)
            )
            assert result.scalar_one_or_none() is not None

        async with db.begin_session() as db_session:
            result = await db_session.execute(
                sa.select(PermissionGroupRow).where(PermissionGroupRow.id == pg_id)
            )
            pg_to_delete = result.scalar_one()
            await db_session.delete(pg_to_delete)

        async with db.begin_session() as db_session:
            result = await db_session.execute(
                sa.select(PermissionRow).where(PermissionRow.id == perm_id)
            )
            assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_cascade_delete_permission_group_removes_both(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """When a permission_group is deleted, both permissions and object_permissions should be CASCADE deleted."""
        db = db_with_cleanup

        role_id = uuid4()
        async with db.begin_session() as db_session:
            role = RoleRow(
                id=role_id,
                name="test-role-3",
                description="Test role for combined cascade delete test",
            )
            db_session.add(role)
            await db_session.flush()

            pg = PermissionGroupRow(
                role_id=role_id,
                scope_type=ScopeType.USER,
                scope_id="test-user-id",
            )
            db_session.add(pg)
            await db_session.flush()
            pg_id = pg.id

            perm = PermissionRow(
                permission_group_id=pg_id,
                entity_type=EntityType.IMAGE,
                operation=OperationType.UPDATE,
            )
            db_session.add(perm)
            await db_session.flush()
            perm_id = perm.id

            op = ObjectPermissionRow(
                role_id=role_id,
                permission_group_id=pg_id,
                entity_type=EntityType.SESSION,
                entity_id="test-session-id",
                operation=OperationType.READ,
            )
            db_session.add(op)
            await db_session.flush()
            op_id = op.id

        async with db.begin_session() as db_session:
            result = await db_session.execute(
                sa.select(PermissionRow).where(PermissionRow.id == perm_id)
            )
            assert result.scalar_one_or_none() is not None
            result = await db_session.execute(
                sa.select(ObjectPermissionRow).where(ObjectPermissionRow.id == op_id)
            )
            assert result.scalar_one_or_none() is not None

        async with db.begin_session() as db_session:
            result = await db_session.execute(
                sa.select(PermissionGroupRow).where(PermissionGroupRow.id == pg_id)
            )
            pg_to_delete = result.scalar_one()
            await db_session.delete(pg_to_delete)

        async with db.begin_session() as db_session:
            result = await db_session.execute(
                sa.select(PermissionRow).where(PermissionRow.id == perm_id)
            )
            assert result.scalar_one_or_none() is None
            result = await db_session.execute(
                sa.select(ObjectPermissionRow).where(ObjectPermissionRow.id == op_id)
            )
            assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_role_deletion_does_not_cascade_to_permission_group(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
    ) -> None:
        """Role deletion should NOT cascade to permission_group (no FK constraint)."""
        db = db_with_cleanup

        role_id = uuid4()
        async with db.begin_session() as db_session:
            role = RoleRow(
                id=role_id,
                name="test-role-4",
                description="Test role for no-cascade test",
            )
            db_session.add(role)
            await db_session.flush()

            pg = PermissionGroupRow(
                role_id=role_id,
                scope_type=ScopeType.GLOBAL,
                scope_id="global",
            )
            db_session.add(pg)
            await db_session.flush()
            pg_id = pg.id

        async with db.begin_session() as db_session:
            result = await db_session.execute(sa.select(RoleRow).where(RoleRow.id == role_id))
            role_to_delete = result.scalar_one()
            await db_session.delete(role_to_delete)

        async with db.begin_session() as db_session:
            result = await db_session.execute(
                sa.select(PermissionGroupRow).where(PermissionGroupRow.id == pg_id)
            )
            assert result.scalar_one_or_none() is not None
