"""Integration tests for RBAC entity revoker with real database."""

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
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base.rbac.revoker import (
    RBACRevoker,
    execute_rbac_revoker,
)
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


# =============================================================================
# Tables List
# =============================================================================

REVOKER_TABLES = [
    RoleRow,
    ObjectPermissionRow,
    AssociationScopesEntitiesRow,
]


# =============================================================================
# Data Classes for Fixtures
# =============================================================================


@dataclass
class SingleEntityWithRoleContext:
    """Context with single entity granted to a role."""

    entity_id: ObjectId
    entity_scope_id: ScopeId
    role_id: UUID


@dataclass
class TwoEntitiesWithRoleContext:
    """Context with two entities granted to the same role."""

    entity_id1: ObjectId
    entity_id2: ObjectId
    entity_scope_id: ScopeId
    role_id: UUID


@dataclass
class EntityWithTwoRolesContext:
    """Context with entity granted to two different roles."""

    entity_id: ObjectId
    entity_scope_id: ScopeId
    role_id1: UUID
    role_id2: UUID


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def create_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    """Create RBAC revoker test tables."""
    async with with_tables(database_connection, REVOKER_TABLES):  # type: ignore[arg-type]
        yield


# =============================================================================
# Tests
# =============================================================================


class TestRevokerBasic:
    """Basic tests for revoker operations."""

    @pytest.fixture
    async def single_entity_with_role(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[SingleEntityWithRoleContext, None]:
        """Create entity with role having object permissions."""
        user_id = str(uuid.uuid4())
        entity_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=user_id)
        entity_id = ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(uuid.uuid4()))

        role_id: UUID

        async with database_connection.begin_session_read_committed() as db_sess:
            # Create role
            role = RoleRow(
                id=uuid.uuid4(),
                name="test-role",
                source=RoleSource.SYSTEM,
            )
            db_sess.add(role)
            await db_sess.flush()

            # Create scope-entity association
            assoc_row = AssociationScopesEntitiesRow(
                scope_type=entity_scope_id.scope_type,
                scope_id=entity_scope_id.scope_id,
                entity_type=entity_id.entity_type,
                entity_id=entity_id.entity_id,
            )
            db_sess.add(assoc_row)

            # Create object permissions
            for op in [OperationType.READ, OperationType.UPDATE]:
                obj_perm = ObjectPermissionRow(
                    role_id=role.id,
                    entity_type=entity_id.entity_type,
                    entity_id=entity_id.entity_id,
                    operation=op,
                )
                db_sess.add(obj_perm)
            await db_sess.flush()

            role_id = role.id

        yield SingleEntityWithRoleContext(
            entity_id=entity_id,
            entity_scope_id=entity_scope_id,
            role_id=role_id,
        )

    async def test_revoker_removes_object_permissions(
        self,
        database_connection: ExtendedAsyncSAEngine,
        single_entity_with_role: SingleEntityWithRoleContext,
    ) -> None:
        """Test that revoker removes object permissions from specified role."""
        ctx = single_entity_with_role

        async with database_connection.begin_session_read_committed() as db_sess:
            # Verify initial state
            obj_perm_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ObjectPermissionRow)
            )
            assert obj_perm_count == 2

            # Execute revoke
            revoker = RBACRevoker(
                entity_id=ctx.entity_id,
                target_role_ids=[ctx.role_id],
                operations=None,  # Revoke all operations
            )
            await execute_rbac_revoker(db_sess, revoker)

            # Verify object permissions deleted
            obj_perm_count_after = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ObjectPermissionRow)
            )
            assert obj_perm_count_after == 0

    async def test_revoker_with_empty_role_ids_does_nothing(
        self,
        database_connection: ExtendedAsyncSAEngine,
        single_entity_with_role: SingleEntityWithRoleContext,
    ) -> None:
        """Test that revoker with empty role_ids does nothing."""
        ctx = single_entity_with_role

        async with database_connection.begin_session_read_committed() as db_sess:
            # Execute revoke with empty role_ids
            revoker = RBACRevoker(
                entity_id=ctx.entity_id,
                target_role_ids=[],
                operations=None,
            )
            await execute_rbac_revoker(db_sess, revoker)

            # Verify object permissions still exist
            obj_perm_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ObjectPermissionRow)
            )
            assert obj_perm_count == 2

    async def test_revoker_removes_only_specified_operations(
        self,
        database_connection: ExtendedAsyncSAEngine,
        single_entity_with_role: SingleEntityWithRoleContext,
    ) -> None:
        """Test that revoker only removes specified operations."""
        ctx = single_entity_with_role

        async with database_connection.begin_session_read_committed() as db_sess:
            # Execute revoke for READ only
            revoker = RBACRevoker(
                entity_id=ctx.entity_id,
                target_role_ids=[ctx.role_id],
                operations=[OperationType.READ],
            )
            await execute_rbac_revoker(db_sess, revoker)

            # Verify UPDATE still exists
            remaining_perms = (await db_sess.scalars(sa.select(ObjectPermissionRow))).all()
            assert len(remaining_perms) == 1
            assert remaining_perms[0].operation == OperationType.UPDATE

    async def test_revoker_with_none_operations_removes_all(
        self,
        database_connection: ExtendedAsyncSAEngine,
        single_entity_with_role: SingleEntityWithRoleContext,
    ) -> None:
        """Test that operations=None revokes all operations."""
        ctx = single_entity_with_role

        async with database_connection.begin_session_read_committed() as db_sess:
            # Execute revoke with operations=None
            revoker = RBACRevoker(
                entity_id=ctx.entity_id,
                target_role_ids=[ctx.role_id],
                operations=None,
            )
            await execute_rbac_revoker(db_sess, revoker)

            # Verify no permissions remain
            obj_perm_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ObjectPermissionRow)
            )
            assert obj_perm_count == 0


class TestRevokerMultipleRoles:
    """Tests for revoker with multiple roles."""

    @pytest.fixture
    async def entity_with_two_roles(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[EntityWithTwoRolesContext, None]:
        """Create entity granted to two different roles."""
        user_id = str(uuid.uuid4())
        entity_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=user_id)
        entity_id = ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(uuid.uuid4()))

        role_id1: UUID
        role_id2: UUID

        async with database_connection.begin_session_read_committed() as db_sess:
            # Create two roles
            role1 = RoleRow(
                id=uuid.uuid4(),
                name="role-1",
                source=RoleSource.SYSTEM,
            )
            role2 = RoleRow(
                id=uuid.uuid4(),
                name="role-2",
                source=RoleSource.SYSTEM,
            )
            db_sess.add(role1)
            db_sess.add(role2)
            await db_sess.flush()

            # Create scope-entity association
            assoc_row = AssociationScopesEntitiesRow(
                scope_type=entity_scope_id.scope_type,
                scope_id=entity_scope_id.scope_id,
                entity_type=entity_id.entity_type,
                entity_id=entity_id.entity_id,
            )
            db_sess.add(assoc_row)

            # Create object permissions for both roles
            for role in [role1, role2]:
                obj_perm = ObjectPermissionRow(
                    role_id=role.id,
                    entity_type=entity_id.entity_type,
                    entity_id=entity_id.entity_id,
                    operation=OperationType.READ,
                )
                db_sess.add(obj_perm)
            await db_sess.flush()

            role_id1 = role1.id
            role_id2 = role2.id

        yield EntityWithTwoRolesContext(
            entity_id=entity_id,
            entity_scope_id=entity_scope_id,
            role_id1=role_id1,
            role_id2=role_id2,
        )

    async def test_revoker_revokes_from_multiple_roles(
        self,
        database_connection: ExtendedAsyncSAEngine,
        entity_with_two_roles: EntityWithTwoRolesContext,
    ) -> None:
        """Test that revoker can revoke from multiple roles at once."""
        ctx = entity_with_two_roles

        async with database_connection.begin_session_read_committed() as db_sess:
            # Execute revoke for both roles
            revoker = RBACRevoker(
                entity_id=ctx.entity_id,
                target_role_ids=[ctx.role_id1, ctx.role_id2],
                operations=None,
            )
            await execute_rbac_revoker(db_sess, revoker)

            # Verify no permissions remain
            obj_perm_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ObjectPermissionRow)
            )
            assert obj_perm_count == 0

    async def test_revoker_revokes_from_single_role_preserves_other(
        self,
        database_connection: ExtendedAsyncSAEngine,
        entity_with_two_roles: EntityWithTwoRolesContext,
    ) -> None:
        """Test that revoking from one role preserves other role's permissions."""
        ctx = entity_with_two_roles

        async with database_connection.begin_session_read_committed() as db_sess:
            # Execute revoke for role1 only
            revoker = RBACRevoker(
                entity_id=ctx.entity_id,
                target_role_ids=[ctx.role_id1],
                operations=None,
            )
            await execute_rbac_revoker(db_sess, revoker)

            # Verify role2's permissions preserved
            remaining_perms = (await db_sess.scalars(sa.select(ObjectPermissionRow))).all()
            assert len(remaining_perms) == 1
            assert remaining_perms[0].role_id == ctx.role_id2


class TestRevokerIdempotent:
    """Tests for idempotent behavior of RBAC entity revoker."""

    @pytest.fixture
    async def single_entity_with_role(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[SingleEntityWithRoleContext, None]:
        """Create entity with role having object permissions."""
        user_id = str(uuid.uuid4())
        entity_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=user_id)
        entity_id = ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(uuid.uuid4()))

        role_id: UUID

        async with database_connection.begin_session_read_committed() as db_sess:
            role = RoleRow(
                id=uuid.uuid4(),
                name="test-role",
                source=RoleSource.SYSTEM,
            )
            db_sess.add(role)
            await db_sess.flush()

            # Create scope-entity association
            assoc_row = AssociationScopesEntitiesRow(
                scope_type=entity_scope_id.scope_type,
                scope_id=entity_scope_id.scope_id,
                entity_type=entity_id.entity_type,
                entity_id=entity_id.entity_id,
            )
            db_sess.add(assoc_row)

            obj_perm = ObjectPermissionRow(
                role_id=role.id,
                entity_type=entity_id.entity_type,
                entity_id=entity_id.entity_id,
                operation=OperationType.READ,
            )
            db_sess.add(obj_perm)
            await db_sess.flush()

            role_id = role.id

        yield SingleEntityWithRoleContext(
            entity_id=entity_id,
            entity_scope_id=entity_scope_id,
            role_id=role_id,
        )

    async def test_revoker_is_idempotent(
        self,
        database_connection: ExtendedAsyncSAEngine,
        single_entity_with_role: SingleEntityWithRoleContext,
    ) -> None:
        """Test that revoking same permissions twice is idempotent."""
        ctx = single_entity_with_role

        async with database_connection.begin_session_read_committed() as db_sess:
            revoker = RBACRevoker(
                entity_id=ctx.entity_id,
                target_role_ids=[ctx.role_id],
                operations=None,
            )

            # First revoke
            await execute_rbac_revoker(db_sess, revoker)

            # Verify first revoke deleted permissions
            obj_perm_count_after_first = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ObjectPermissionRow)
            )
            assert obj_perm_count_after_first == 0

            # Second revoke (should do nothing)
            await execute_rbac_revoker(db_sess, revoker)

            # Verify final state is same as after first revoke
            obj_perm_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ObjectPermissionRow)
            )
            assert obj_perm_count == 0
