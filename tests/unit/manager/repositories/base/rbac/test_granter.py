"""Integration tests for RBAC entity granter with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

from ai.backend.common.data.permission.types import OperationType
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.types import (
    EntityType,
    RoleSource,
    ScopeType,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base.rbac.granter import (
    RBACGranter,
    execute_rbac_granter,
)
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


# =============================================================================
# Tables List
# =============================================================================

GRANTER_TABLES = [
    RoleRow,
    ObjectPermissionRow,
]


# =============================================================================
# Data Classes for Fixtures
# =============================================================================


@dataclass
class GranterTestContext:
    """Context data for granter tests."""

    entity_scope_id: ScopeId
    entity_id: ObjectId


@dataclass
class SingleRoleContext(GranterTestContext):
    """Context with a single role."""

    role_id: UUID


@dataclass
class MultiRoleContext(GranterTestContext):
    """Context with multiple roles."""

    role_ids: list[UUID]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def create_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    """Create RBAC granter test tables."""
    async with with_tables(database_connection, GRANTER_TABLES):  # type: ignore[arg-type]
        yield


# =============================================================================
# Tests
# =============================================================================


class TestGranterBasic:
    """Basic tests for granter operations."""

    @pytest.fixture
    async def single_role(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[SingleRoleContext, None]:
        """Create a single role for granter testing."""
        entity_owner_id = str(uuid.uuid4())
        entity_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=entity_owner_id)
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
            role_id = role.id

        yield SingleRoleContext(
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
        """Create context without any roles (for testing empty role_ids)."""
        entity_owner_id = str(uuid.uuid4())
        entity_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=entity_owner_id)
        entity_id = ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(uuid.uuid4()))

        yield GranterTestContext(
            entity_scope_id=entity_scope_id,
            entity_id=entity_id,
        )

    async def test_granter_creates_object_permissions(
        self,
        database_connection: ExtendedAsyncSAEngine,
        single_role: SingleRoleContext,
    ) -> None:
        """Test that granter creates object permissions for specified role."""
        ctx = single_role

        async with database_connection.begin_session_read_committed() as db_sess:
            granter = RBACGranter(
                granted_entity_id=ctx.entity_id,
                granted_entity_scope_id=ctx.entity_scope_id,
                target_role_ids=[ctx.role_id],
                operations=[OperationType.READ, OperationType.UPDATE],
            )
            await execute_rbac_granter(db_sess, granter)

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

    async def test_granter_with_empty_role_ids(
        self,
        database_connection: ExtendedAsyncSAEngine,
        empty_context: GranterTestContext,
    ) -> None:
        """Test granter behavior with empty target_role_ids."""
        ctx = empty_context

        async with database_connection.begin_session_read_committed() as db_sess:
            granter = RBACGranter(
                granted_entity_id=ctx.entity_id,
                granted_entity_scope_id=ctx.entity_scope_id,
                target_role_ids=[],
                operations=[OperationType.READ],
            )
            await execute_rbac_granter(db_sess, granter)

            # Verify no object permissions were created
            obj_perm_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ObjectPermissionRow)
            )
            assert obj_perm_count == 0


class TestGranterMultipleRoles:
    """Tests for granter with multiple roles."""

    @pytest.fixture
    async def multi_role_context(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[MultiRoleContext, None]:
        """Create multiple roles for granter testing."""
        entity_owner_id = str(uuid.uuid4())
        entity_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=entity_owner_id)
        entity_id = ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(uuid.uuid4()))

        role_ids: list[UUID] = []

        async with database_connection.begin_session_read_committed() as db_sess:
            for i in range(3):
                role = RoleRow(
                    id=uuid.uuid4(),
                    name=f"test-role-{i}",
                    source=RoleSource.SYSTEM,
                )
                db_sess.add(role)
                await db_sess.flush()
                role_ids.append(role.id)

        yield MultiRoleContext(
            entity_scope_id=entity_scope_id,
            entity_id=entity_id,
            role_ids=role_ids,
        )

    async def test_granter_grants_to_multiple_roles(
        self,
        database_connection: ExtendedAsyncSAEngine,
        multi_role_context: MultiRoleContext,
    ) -> None:
        """Test that granter grants permissions to all specified roles."""
        ctx = multi_role_context

        async with database_connection.begin_session_read_committed() as db_sess:
            granter = RBACGranter(
                granted_entity_id=ctx.entity_id,
                granted_entity_scope_id=ctx.entity_scope_id,
                target_role_ids=ctx.role_ids,
                operations=[OperationType.READ],
            )
            await execute_rbac_granter(db_sess, granter)

            # Verify object permissions were created for all roles
            obj_perm_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ObjectPermissionRow)
            )
            assert obj_perm_count == 3  # 1 operation x 3 roles

            obj_perms = (await db_sess.scalars(sa.select(ObjectPermissionRow))).all()
            granted_role_ids = {perm.role_id for perm in obj_perms}
            assert granted_role_ids == set(ctx.role_ids)


class TestGranterMultipleOperations:
    """Tests for granter with multiple operations."""

    @pytest.fixture
    async def single_role(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[SingleRoleContext, None]:
        """Create a single role for granter testing."""
        entity_owner_id = str(uuid.uuid4())
        entity_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=entity_owner_id)
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
            role_id = role.id

        yield SingleRoleContext(
            entity_scope_id=entity_scope_id,
            entity_id=entity_id,
            role_id=role_id,
        )

    async def test_granter_with_all_operations(
        self,
        database_connection: ExtendedAsyncSAEngine,
        single_role: SingleRoleContext,
    ) -> None:
        """Test granter with all operation types."""
        ctx = single_role
        all_operations = [
            OperationType.READ,
            OperationType.UPDATE,
            OperationType.SOFT_DELETE,
            OperationType.HARD_DELETE,
        ]

        async with database_connection.begin_session_read_committed() as db_sess:
            granter = RBACGranter(
                granted_entity_id=ctx.entity_id,
                granted_entity_scope_id=ctx.entity_scope_id,
                target_role_ids=[ctx.role_id],
                operations=all_operations,
            )
            await execute_rbac_granter(db_sess, granter)

            # Verify all operations were granted
            obj_perms = (await db_sess.scalars(sa.select(ObjectPermissionRow))).all()
            assert len(obj_perms) == len(all_operations)
            granted_ops = {perm.operation for perm in obj_perms}
            assert granted_ops == set(all_operations)

    async def test_granter_with_empty_operations(
        self,
        database_connection: ExtendedAsyncSAEngine,
        single_role: SingleRoleContext,
    ) -> None:
        """Test granter with empty operations list."""
        ctx = single_role

        async with database_connection.begin_session_read_committed() as db_sess:
            granter = RBACGranter(
                granted_entity_id=ctx.entity_id,
                granted_entity_scope_id=ctx.entity_scope_id,
                target_role_ids=[ctx.role_id],
                operations=[],
            )
            await execute_rbac_granter(db_sess, granter)

            # Verify no object permissions were created
            obj_perm_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ObjectPermissionRow)
            )
            assert obj_perm_count == 0


class TestGranterIdempotent:
    """Tests for idempotent behavior of RBAC entity granter."""

    @pytest.fixture
    async def single_role(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[SingleRoleContext, None]:
        """Create a single role for granter testing."""
        entity_owner_id = str(uuid.uuid4())
        entity_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=entity_owner_id)
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
            role_id = role.id

        yield SingleRoleContext(
            entity_scope_id=entity_scope_id,
            entity_id=entity_id,
            role_id=role_id,
        )

    async def test_granter_raises_on_duplicate_grant(
        self,
        database_connection: ExtendedAsyncSAEngine,
        single_role: SingleRoleContext,
    ) -> None:
        """Test that granting same entity to same roles twice raises IntegrityError.

        Duplicate object permission grants are detected via unique constraint and
        raise an error rather than being silently ignored, ensuring explicit error
        handling by the caller.
        """
        ctx = single_role

        # First grant in separate session (committed)
        async with database_connection.begin_session_read_committed() as db_sess:
            granter = RBACGranter(
                granted_entity_id=ctx.entity_id,
                granted_entity_scope_id=ctx.entity_scope_id,
                target_role_ids=[ctx.role_id],
                operations=[OperationType.READ, OperationType.UPDATE],
            )
            await execute_rbac_granter(db_sess, granter)

        # Verify initial state
        async with database_connection.begin_readonly_session_read_committed() as db_sess:
            obj_perm_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ObjectPermissionRow)
            )
            assert obj_perm_count == 2

        # Second grant (duplicate) - should raise IntegrityError
        with pytest.raises(IntegrityError):
            async with database_connection.begin_session_read_committed() as db_sess:
                await execute_rbac_granter(db_sess, granter)

    async def test_granter_grants_to_multiple_roles_sequentially(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test that same entity can be granted to multiple roles sequentially."""
        entity_owner_id = str(uuid.uuid4())
        entity_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=entity_owner_id)
        entity_id = ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(uuid.uuid4()))

        async with database_connection.begin_session_read_committed() as db_sess:
            # Create multiple roles
            role_ids: list[UUID] = []
            for i in range(3):
                role = RoleRow(
                    id=uuid.uuid4(),
                    name=f"test-role-{i}",
                    source=RoleSource.SYSTEM,
                )
                db_sess.add(role)
                await db_sess.flush()
                role_ids.append(role.id)

            # Grant entity to each role individually
            for role_id in role_ids:
                granter = RBACGranter(
                    granted_entity_id=entity_id,
                    granted_entity_scope_id=entity_scope_id,
                    target_role_ids=[role_id],
                    operations=[OperationType.READ],
                )
                await execute_rbac_granter(db_sess, granter)

            # Verify object permissions created for all roles
            obj_perm_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ObjectPermissionRow)
            )
            assert obj_perm_count == 3
