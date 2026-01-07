"""Integration tests for RBAC entity granter with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
import sqlalchemy as sa

from ai.backend.common.data.permission.types import OperationType
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.types import (
    EntityType,
    RoleSource,
    ScopeType,
)
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission_group import PermissionGroupRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base.rbac_entity.granter import (
    Granter,
    execute_granter,
)
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


# =============================================================================
# Tables List
# =============================================================================

GRANTER_TABLES = [
    RoleRow,
    PermissionGroupRow,
    ObjectPermissionRow,
    AssociationScopesEntitiesRow,
]


# =============================================================================
# Data Classes for Fixtures
# =============================================================================


@dataclass
class GranterTestContext:
    """Context data for granter tests."""

    target_scope_id: ScopeId
    entity_scope_id: ScopeId
    entity_id: ObjectId


@dataclass
class RoleWithPermGroupContext(GranterTestContext):
    """Context with a single system role and permission group."""

    role_id: UUID


@dataclass
class MultiRoleContext(GranterTestContext):
    """Context with multiple system roles."""

    role_ids: list[UUID]


@dataclass
class MixedRoleContext(GranterTestContext):
    """Context with both system and custom roles."""

    system_role_id: UUID
    custom_role_id: UUID


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def create_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    """Create RBAC granter test tables."""
    async with with_tables(database_connection, GRANTER_TABLES):
        yield


# =============================================================================
# Tests
# =============================================================================


class TestGranterBasic:
    """Basic tests for granter operations."""

    @pytest.fixture
    async def role_with_perm_group(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[RoleWithPermGroupContext, None]:
        """Create a system role with permission group for target scope."""
        target_user_id = str(uuid.uuid4())
        target_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=target_user_id)

        entity_owner_id = str(uuid.uuid4())
        entity_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=entity_owner_id)
        entity_id = ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(uuid.uuid4()))

        role_id: UUID
        async with database_connection.begin_session() as db_sess:
            role = RoleRow(
                id=uuid.uuid4(),
                name="target-user-system-role",
                source=RoleSource.SYSTEM,
            )
            db_sess.add(role)
            await db_sess.flush()

            perm_group = PermissionGroupRow(
                role_id=role.id,
                scope_type=target_scope_id.scope_type,
                scope_id=target_scope_id.scope_id,
            )
            db_sess.add(perm_group)
            await db_sess.flush()
            role_id = role.id

        yield RoleWithPermGroupContext(
            target_scope_id=target_scope_id,
            entity_scope_id=entity_scope_id,
            entity_id=entity_id,
            role_id=role_id,
        )

    @pytest.fixture
    async def empty_context(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[GranterTestContext, None]:
        """Create context without any roles (for testing graceful handling)."""
        target_user_id = str(uuid.uuid4())
        target_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=target_user_id)

        entity_owner_id = str(uuid.uuid4())
        entity_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=entity_owner_id)
        entity_id = ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(uuid.uuid4()))

        yield GranterTestContext(
            target_scope_id=target_scope_id,
            entity_scope_id=entity_scope_id,
            entity_id=entity_id,
        )

    async def test_granter_creates_object_permissions_and_association(
        self,
        database_connection: ExtendedAsyncSAEngine,
        role_with_perm_group: RoleWithPermGroupContext,
    ) -> None:
        """Test that granter creates object permissions and scope-entity association."""
        ctx = role_with_perm_group

        async with database_connection.begin_session() as db_sess:
            granter = Granter(
                granted_entity_id=ctx.entity_id,
                granted_entity_scope_id=ctx.entity_scope_id,
                target_scope_id=ctx.target_scope_id,
                operations=[OperationType.READ, OperationType.UPDATE],
            )
            await execute_granter(db_sess, granter)

            # Verify object permissions were created
            obj_perm_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ObjectPermissionRow)
            )
            assert obj_perm_count == 2  # READ and UPDATE

            # Verify object permission details
            obj_perms = (await db_sess.scalars(sa.select(ObjectPermissionRow))).all()
            operations = {perm.operation for perm in obj_perms}
            assert operations == {OperationType.READ, OperationType.UPDATE}
            for perm in obj_perms:
                assert perm.role_id == ctx.role_id
                assert perm.entity_type == EntityType.VFOLDER
                assert perm.entity_id == ctx.entity_id.entity_id

            # Verify scope-entity association was created
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 1

            assoc_row = await db_sess.scalar(sa.select(AssociationScopesEntitiesRow))
            assert assoc_row is not None
            assert assoc_row.scope_type == ctx.target_scope_id.scope_type
            assert assoc_row.scope_id == ctx.target_scope_id.scope_id
            assert assoc_row.entity_type == ctx.entity_id.entity_type
            assert assoc_row.entity_id == ctx.entity_id.entity_id

    async def test_granter_creates_permission_group_for_entity_scope(
        self,
        database_connection: ExtendedAsyncSAEngine,
        role_with_perm_group: RoleWithPermGroupContext,
    ) -> None:
        """Test that granter ensures permission group exists for entity's original scope."""
        ctx = role_with_perm_group

        async with database_connection.begin_session() as db_sess:
            granter = Granter(
                granted_entity_id=ctx.entity_id,
                granted_entity_scope_id=ctx.entity_scope_id,
                target_scope_id=ctx.target_scope_id,
                operations=[OperationType.READ],
            )
            await execute_granter(db_sess, granter)

            # Verify permission group was created for entity scope
            pg_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(PermissionGroupRow)
            )
            assert pg_count == 2

            # Verify the new permission group
            entity_scope_pg = await db_sess.scalar(
                sa.select(PermissionGroupRow).where(
                    sa.and_(
                        PermissionGroupRow.scope_id == ctx.entity_scope_id.scope_id,
                        PermissionGroupRow.scope_type == ctx.entity_scope_id.scope_type,
                    )
                )
            )
            assert entity_scope_pg is not None
            assert entity_scope_pg.role_id == ctx.role_id

    async def test_granter_with_no_matching_system_role(
        self,
        database_connection: ExtendedAsyncSAEngine,
        empty_context: GranterTestContext,
    ) -> None:
        """Test granter behavior when no system role exists for target scope."""
        ctx = empty_context

        async with database_connection.begin_session() as db_sess:
            granter = Granter(
                granted_entity_id=ctx.entity_id,
                granted_entity_scope_id=ctx.entity_scope_id,
                target_scope_id=ctx.target_scope_id,
                operations=[OperationType.READ],
            )
            await execute_granter(db_sess, granter)

            # Verify no object permissions were created (no roles to grant to)
            obj_perm_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ObjectPermissionRow)
            )
            assert obj_perm_count == 0

            # Verify association was still created
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 1


class TestGranterMultipleRoles:
    """Tests for granter with multiple system roles."""

    @pytest.fixture
    async def multi_role_context(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[MultiRoleContext, None]:
        """Create multiple system roles with permission groups for target scope."""
        target_user_id = str(uuid.uuid4())
        target_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=target_user_id)

        entity_owner_id = str(uuid.uuid4())
        entity_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=entity_owner_id)
        entity_id = ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(uuid.uuid4()))

        role_ids: list[UUID] = []

        async with database_connection.begin_session() as db_sess:
            for i in range(3):
                role = RoleRow(
                    id=uuid.uuid4(),
                    name=f"system-role-{i}",
                    source=RoleSource.SYSTEM,
                )
                db_sess.add(role)
                await db_sess.flush()
                role_ids.append(role.id)

                perm_group = PermissionGroupRow(
                    role_id=role.id,
                    scope_type=target_scope_id.scope_type,
                    scope_id=target_scope_id.scope_id,
                )
                db_sess.add(perm_group)
                await db_sess.flush()

        yield MultiRoleContext(
            target_scope_id=target_scope_id,
            entity_scope_id=entity_scope_id,
            entity_id=entity_id,
            role_ids=role_ids,
        )

    @pytest.fixture
    async def mixed_role_context(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[MixedRoleContext, None]:
        """Create one system role and one custom role with permission groups."""
        target_user_id = str(uuid.uuid4())
        target_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=target_user_id)

        entity_owner_id = str(uuid.uuid4())
        entity_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=entity_owner_id)
        entity_id = ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(uuid.uuid4()))

        system_role_id: UUID
        custom_role_id: UUID

        async with database_connection.begin_session() as db_sess:
            system_role = RoleRow(
                id=uuid.uuid4(),
                name="system-role",
                source=RoleSource.SYSTEM,
            )
            db_sess.add(system_role)

            custom_role = RoleRow(
                id=uuid.uuid4(),
                name="custom-role",
                source=RoleSource.CUSTOM,
            )
            db_sess.add(custom_role)
            await db_sess.flush()

            for role in [system_role, custom_role]:
                perm_group = PermissionGroupRow(
                    role_id=role.id,
                    scope_type=target_scope_id.scope_type,
                    scope_id=target_scope_id.scope_id,
                )
                db_sess.add(perm_group)
            await db_sess.flush()

            system_role_id = system_role.id
            custom_role_id = custom_role.id

        yield MixedRoleContext(
            target_scope_id=target_scope_id,
            entity_scope_id=entity_scope_id,
            entity_id=entity_id,
            system_role_id=system_role_id,
            custom_role_id=custom_role_id,
        )

    async def test_granter_grants_to_multiple_system_roles(
        self,
        database_connection: ExtendedAsyncSAEngine,
        multi_role_context: MultiRoleContext,
    ) -> None:
        """Test that granter grants permissions to all system roles for a scope."""
        ctx = multi_role_context

        async with database_connection.begin_session() as db_sess:
            granter = Granter(
                granted_entity_id=ctx.entity_id,
                granted_entity_scope_id=ctx.entity_scope_id,
                target_scope_id=ctx.target_scope_id,
                operations=[OperationType.READ],
            )
            await execute_granter(db_sess, granter)

            # Verify object permissions were created for all roles
            obj_perm_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ObjectPermissionRow)
            )
            assert obj_perm_count == 3  # 1 operation x 3 roles

            obj_perms = (await db_sess.scalars(sa.select(ObjectPermissionRow))).all()
            granted_role_ids = {perm.role_id for perm in obj_perms}
            assert granted_role_ids == set(ctx.role_ids)

    async def test_granter_ignores_custom_roles(
        self,
        database_connection: ExtendedAsyncSAEngine,
        mixed_role_context: MixedRoleContext,
    ) -> None:
        """Test that granter only grants to system roles, not custom roles."""
        ctx = mixed_role_context

        async with database_connection.begin_session() as db_sess:
            granter = Granter(
                granted_entity_id=ctx.entity_id,
                granted_entity_scope_id=ctx.entity_scope_id,
                target_scope_id=ctx.target_scope_id,
                operations=[OperationType.READ],
            )
            await execute_granter(db_sess, granter)

            # Verify only system role got permissions
            obj_perms = (await db_sess.scalars(sa.select(ObjectPermissionRow))).all()
            assert len(obj_perms) == 1
            assert obj_perms[0].role_id == ctx.system_role_id


class TestGranterMultipleOperations:
    """Tests for granter with multiple operations."""

    @pytest.fixture
    async def role_with_perm_group(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[RoleWithPermGroupContext, None]:
        """Create a system role with permission group for target scope."""
        target_user_id = str(uuid.uuid4())
        target_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=target_user_id)

        entity_owner_id = str(uuid.uuid4())
        entity_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=entity_owner_id)
        entity_id = ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(uuid.uuid4()))

        role_id: UUID
        async with database_connection.begin_session() as db_sess:
            role = RoleRow(
                id=uuid.uuid4(),
                name="system-role",
                source=RoleSource.SYSTEM,
            )
            db_sess.add(role)
            await db_sess.flush()

            perm_group = PermissionGroupRow(
                role_id=role.id,
                scope_type=target_scope_id.scope_type,
                scope_id=target_scope_id.scope_id,
            )
            db_sess.add(perm_group)
            await db_sess.flush()
            role_id = role.id

        yield RoleWithPermGroupContext(
            target_scope_id=target_scope_id,
            entity_scope_id=entity_scope_id,
            entity_id=entity_id,
            role_id=role_id,
        )

    async def test_granter_with_all_operations(
        self,
        database_connection: ExtendedAsyncSAEngine,
        role_with_perm_group: RoleWithPermGroupContext,
    ) -> None:
        """Test granter with all operation types."""
        ctx = role_with_perm_group
        all_operations = [
            OperationType.READ,
            OperationType.UPDATE,
            OperationType.SOFT_DELETE,
            OperationType.HARD_DELETE,
        ]

        async with database_connection.begin_session() as db_sess:
            granter = Granter(
                granted_entity_id=ctx.entity_id,
                granted_entity_scope_id=ctx.entity_scope_id,
                target_scope_id=ctx.target_scope_id,
                operations=all_operations,
            )
            await execute_granter(db_sess, granter)

            # Verify all operations were granted
            obj_perms = (await db_sess.scalars(sa.select(ObjectPermissionRow))).all()
            assert len(obj_perms) == len(all_operations)
            granted_ops = {perm.operation for perm in obj_perms}
            assert granted_ops == set(all_operations)

    async def test_granter_with_empty_operations(
        self,
        database_connection: ExtendedAsyncSAEngine,
        role_with_perm_group: RoleWithPermGroupContext,
    ) -> None:
        """Test granter with empty operations list."""
        ctx = role_with_perm_group

        async with database_connection.begin_session() as db_sess:
            granter = Granter(
                granted_entity_id=ctx.entity_id,
                granted_entity_scope_id=ctx.entity_scope_id,
                target_scope_id=ctx.target_scope_id,
                operations=[],
            )
            await execute_granter(db_sess, granter)

            # Verify no object permissions were created
            obj_perm_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ObjectPermissionRow)
            )
            assert obj_perm_count == 0

            # Verify association was still created
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 1
