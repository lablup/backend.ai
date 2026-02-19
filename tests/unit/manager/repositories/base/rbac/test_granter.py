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

from ai.backend.common.data.permission.types import OperationType, RelationType
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.types import (
    EntityType,
    RoleSource,
    ScopeType,
)
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
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
    PermissionRow,
    AssociationScopesEntitiesRow,
]


# =============================================================================
# Data Classes for Fixtures
# =============================================================================


@dataclass
class GranterTestContext:
    """Context data for granter tests."""

    entity_scope_type: ScopeType
    entity_id: ObjectId
    target_scope_id: ScopeId


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
        entity_id = ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(uuid.uuid4()))
        target_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=str(uuid.uuid4()))

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
            entity_scope_type=ScopeType.VFOLDER,
            entity_id=entity_id,
            target_scope_id=target_scope_id,
            role_id=role_id,
        )

    @pytest.fixture
    async def empty_context(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[GranterTestContext, None]:
        """Create context without any roles (for testing empty role_ids)."""
        entity_id = ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(uuid.uuid4()))
        target_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=str(uuid.uuid4()))

        yield GranterTestContext(
            entity_scope_type=ScopeType.VFOLDER,
            entity_id=entity_id,
            target_scope_id=target_scope_id,
        )

    async def test_granter_creates_permissions_and_ref_edge(
        self,
        database_connection: ExtendedAsyncSAEngine,
        single_role: SingleRoleContext,
    ) -> None:
        """Test that granter creates ref edge and permissions for specified role."""
        ctx = single_role

        async with database_connection.begin_session_read_committed() as db_sess:
            granter = RBACGranter(
                granted_entity_id=ctx.entity_id,
                granted_entity_scope_type=ctx.entity_scope_type,
                target_scope_id=ctx.target_scope_id,
                target_role_ids=[ctx.role_id],
                operations=[OperationType.READ, OperationType.UPDATE],
            )
            await execute_rbac_granter(db_sess, granter)

            # Verify ref edge was created in association_scopes_entities
            assoc = (await db_sess.scalars(sa.select(AssociationScopesEntitiesRow))).one()
            assert assoc.scope_type == ctx.target_scope_id.scope_type
            assert assoc.scope_id == ctx.target_scope_id.scope_id
            assert assoc.entity_type == ctx.entity_id.entity_type
            assert assoc.entity_id == ctx.entity_id.entity_id
            assert assoc.relation_type == RelationType.REF

            # Verify permissions were created
            perm_count = await db_sess.scalar(sa.select(sa.func.count()).select_from(PermissionRow))
            assert perm_count == 2  # READ and UPDATE

            # Verify permission details
            perms = (await db_sess.scalars(sa.select(PermissionRow))).all()
            operations = {perm.operation for perm in perms}
            assert operations == {OperationType.READ, OperationType.UPDATE}
            for perm in perms:
                assert perm.role_id == ctx.role_id
                assert perm.scope_type == ScopeType.VFOLDER
                assert perm.scope_id == ctx.entity_id.entity_id
                assert perm.entity_type == EntityType.VFOLDER

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
                granted_entity_scope_type=ctx.entity_scope_type,
                target_scope_id=ctx.target_scope_id,
                target_role_ids=[],
                operations=[OperationType.READ],
            )
            await execute_rbac_granter(db_sess, granter)

            # Verify no permissions or associations were created
            perm_count = await db_sess.scalar(sa.select(sa.func.count()).select_from(PermissionRow))
            assert perm_count == 0
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 0


class TestGranterMultipleRoles:
    """Tests for granter with multiple roles."""

    @pytest.fixture
    async def multi_role_context(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[MultiRoleContext, None]:
        """Create multiple roles for granter testing."""
        entity_id = ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(uuid.uuid4()))
        target_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=str(uuid.uuid4()))

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
            entity_scope_type=ScopeType.VFOLDER,
            entity_id=entity_id,
            target_scope_id=target_scope_id,
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
                granted_entity_scope_type=ctx.entity_scope_type,
                target_scope_id=ctx.target_scope_id,
                target_role_ids=ctx.role_ids,
                operations=[OperationType.READ],
            )
            await execute_rbac_granter(db_sess, granter)

            # Verify ref edge was created (single edge regardless of role count)
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 1

            # Verify permissions were created for all roles
            perm_count = await db_sess.scalar(sa.select(sa.func.count()).select_from(PermissionRow))
            assert perm_count == 3  # 1 operation x 3 roles

            perms = (await db_sess.scalars(sa.select(PermissionRow))).all()
            granted_role_ids = {perm.role_id for perm in perms}
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
        entity_id = ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(uuid.uuid4()))
        target_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=str(uuid.uuid4()))

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
            entity_scope_type=ScopeType.VFOLDER,
            entity_id=entity_id,
            target_scope_id=target_scope_id,
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
                granted_entity_scope_type=ctx.entity_scope_type,
                target_scope_id=ctx.target_scope_id,
                target_role_ids=[ctx.role_id],
                operations=all_operations,
            )
            await execute_rbac_granter(db_sess, granter)

            # Verify all operations were granted
            perms = (await db_sess.scalars(sa.select(PermissionRow))).all()
            assert len(perms) == len(all_operations)
            granted_ops = {perm.operation for perm in perms}
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
                granted_entity_scope_type=ctx.entity_scope_type,
                target_scope_id=ctx.target_scope_id,
                target_role_ids=[ctx.role_id],
                operations=[],
            )
            await execute_rbac_granter(db_sess, granter)

            # Verify no permissions or associations were created
            perm_count = await db_sess.scalar(sa.select(sa.func.count()).select_from(PermissionRow))
            assert perm_count == 0
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 0


class TestGranterIdempotent:
    """Tests for idempotent behavior of RBAC entity granter."""

    @pytest.fixture
    async def single_role(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[SingleRoleContext, None]:
        """Create a single role for granter testing."""
        entity_id = ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(uuid.uuid4()))
        target_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=str(uuid.uuid4()))

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
            entity_scope_type=ScopeType.VFOLDER,
            entity_id=entity_id,
            target_scope_id=target_scope_id,
            role_id=role_id,
        )

    async def test_granter_raises_on_duplicate_grant(
        self,
        database_connection: ExtendedAsyncSAEngine,
        single_role: SingleRoleContext,
    ) -> None:
        """Test that granting same entity to same roles twice raises IntegrityError.

        Duplicate permission grants are detected via unique constraint and
        raise an error rather than being silently ignored, ensuring explicit error
        handling by the caller.
        """
        ctx = single_role

        # First grant in separate session (committed)
        async with database_connection.begin_session_read_committed() as db_sess:
            granter = RBACGranter(
                granted_entity_id=ctx.entity_id,
                granted_entity_scope_type=ctx.entity_scope_type,
                target_scope_id=ctx.target_scope_id,
                target_role_ids=[ctx.role_id],
                operations=[OperationType.READ, OperationType.UPDATE],
            )
            await execute_rbac_granter(db_sess, granter)

        # Verify initial state
        async with database_connection.begin_readonly_session_read_committed() as db_sess:
            perm_count = await db_sess.scalar(sa.select(sa.func.count()).select_from(PermissionRow))
            assert perm_count == 2

        # Second grant (duplicate) - should raise IntegrityError
        with pytest.raises(IntegrityError):
            async with database_connection.begin_session_read_committed() as db_sess:
                await execute_rbac_granter(db_sess, granter)

    async def test_granter_grants_to_different_scopes_sequentially(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test that same entity can be granted to different scopes sequentially."""
        entity_id = ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(uuid.uuid4()))

        async with database_connection.begin_session_read_committed() as db_sess:
            # Create multiple roles (one per user scope)
            role_ids: list[UUID] = []
            scope_ids: list[ScopeId] = []
            for i in range(3):
                role = RoleRow(
                    id=uuid.uuid4(),
                    name=f"test-role-{i}",
                    source=RoleSource.SYSTEM,
                )
                db_sess.add(role)
                await db_sess.flush()
                role_ids.append(role.id)
                scope_ids.append(ScopeId(scope_type=ScopeType.USER, scope_id=str(uuid.uuid4())))

            # Grant entity to each role with different target scopes
            for role_id, scope_id in zip(role_ids, scope_ids, strict=True):
                granter = RBACGranter(
                    granted_entity_id=entity_id,
                    granted_entity_scope_type=ScopeType.VFOLDER,
                    target_scope_id=scope_id,
                    target_role_ids=[role_id],
                    operations=[OperationType.READ],
                )
                await execute_rbac_granter(db_sess, granter)

            # Verify permissions and associations created for all
            perm_count = await db_sess.scalar(sa.select(sa.func.count()).select_from(PermissionRow))
            assert perm_count == 3
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 3
