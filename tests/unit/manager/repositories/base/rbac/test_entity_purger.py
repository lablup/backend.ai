"""Integration tests for RBAC entity purger with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from uuid import UUID

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.permission.types import OperationType, ScopeType
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.types import (
    EntityType,
    RoleSource,
)
from ai.backend.manager.errors.repository import UnsupportedCompositePrimaryKeyError
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base.rbac.entity_purger import (
    RBACEntity,
    RBACEntityBatchPurger,
    RBACEntityBatchPurgerResult,
    RBACEntityBatchPurgerSpec,
    RBACEntityPurger,
    RBACEntityPurgerResult,
    RBACEntityPurgerSpec,
    execute_rbac_entity_batch_purger,
    execute_rbac_entity_purger,
)
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


# =============================================================================
# Test Row Models
# =============================================================================


class RBACEntityPurgerTestRow(Base):  # type: ignore[misc]
    """ORM model implementing RBACEntityRowProtocol for entity purger testing."""

    __tablename__ = "test_rbac_purger"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(
        GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    owner_scope_type: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    owner_scope_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)

    def scope_id(self) -> ScopeId:
        return ScopeId(scope_type=ScopeType(self.owner_scope_type), scope_id=self.owner_scope_id)

    def entity_id(self) -> ObjectId:
        return ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(self.id))


# =============================================================================
# Purger Spec Implementations
# =============================================================================


class SimpleRBACEntityPurgerSpec(RBACEntityPurgerSpec):
    """Simple spec for entity purger testing."""

    def __init__(self, entity_uuid: UUID) -> None:
        self._entity_uuid = entity_uuid

    def entity(self) -> RBACEntity:
        return RBACEntity(
            entity=ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(self._entity_uuid))
        )

    def scope_type(self) -> ScopeType:
        return ScopeType.VFOLDER


# =============================================================================
# Tables List
# =============================================================================

ENTITY_PURGER_TABLES = [
    RBACEntityPurgerTestRow,
    RoleRow,
    PermissionRow,
    AssociationScopesEntitiesRow,
]


# =============================================================================
# Data Classes for Fixtures
# =============================================================================


@dataclass
class EntityWithAssociationContext:
    """Context with entity row and scope association."""

    entity_uuid: UUID
    user_id: str


@dataclass
class EntityWithPermissionsContext:
    """Context with entity, role, and permissions."""

    entity_uuid: UUID
    user_id: str
    role_id: UUID


@dataclass
class TwoEntitiesContext:
    """Context with two entities sharing same scope."""

    entity_uuid1: UUID
    entity_uuid2: UUID
    user_id: str
    role_id: UUID


@dataclass
class MultiScopeEntityContext:
    """Context with entity shared across multiple scopes."""

    entity_uuid: UUID
    owner_user_id: str
    shared_user_id: str


@dataclass
class EntityWithScopeAssociationsContext:
    """Context with entity that acts as a scope for child entities."""

    entity_uuid: UUID
    user_id: str
    child_entity_ids: list[str]


@dataclass
class BatchEntitiesContext:
    """Context with multiple entities for batch purge testing."""

    entity_uuids: list[UUID]
    user_id: str


@dataclass
class BatchEntitiesWithPermissionsContext:
    """Context with multiple entities and shared role/permissions."""

    entity_uuids: list[UUID]
    user_id: str
    role_id: UUID


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def create_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    """Create RBAC entity purger test tables."""
    async with with_tables(database_connection, ENTITY_PURGER_TABLES):  # type: ignore[arg-type]
        yield


# =============================================================================
# Tests
# =============================================================================


class TestRBACEntityPurgerBasic:
    """Basic tests for entity purger operations."""

    @pytest.fixture
    async def entity_with_association(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[EntityWithAssociationContext, None]:
        """Create entity row and scope association."""
        user_id = str(uuid.uuid4())
        entity_uuid = uuid.uuid4()

        async with database_connection.begin_session_read_committed() as db_sess:
            entity_row = RBACEntityPurgerTestRow(
                id=entity_uuid,
                name="test-entity",
                owner_scope_type=ScopeType.USER.value,
                owner_scope_id=user_id,
            )
            db_sess.add(entity_row)

            assoc_row = AssociationScopesEntitiesRow(
                scope_type=ScopeType.USER,
                scope_id=user_id,
                entity_type=EntityType.VFOLDER,
                entity_id=str(entity_uuid),
            )
            db_sess.add(assoc_row)
            await db_sess.flush()

        yield EntityWithAssociationContext(
            entity_uuid=entity_uuid,
            user_id=user_id,
        )

    async def test_purger_deletes_main_row_and_association(
        self,
        database_connection: ExtendedAsyncSAEngine,
        entity_with_association: EntityWithAssociationContext,
    ) -> None:
        """Test that purger deletes main row and scope-entity association."""
        ctx = entity_with_association

        async with database_connection.begin_session_read_committed() as db_sess:
            spec = SimpleRBACEntityPurgerSpec(entity_uuid=ctx.entity_uuid)
            purger: RBACEntityPurger[RBACEntityPurgerTestRow] = RBACEntityPurger(
                row_class=RBACEntityPurgerTestRow,
                pk_value=ctx.entity_uuid,
                spec=spec,
            )
            result = await execute_rbac_entity_purger(db_sess, purger)

            # Verify result
            assert isinstance(result, RBACEntityPurgerResult)
            assert result.row.id == ctx.entity_uuid
            assert result.row.name == "test-entity"

            # Verify main row deleted
            entity_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACEntityPurgerTestRow)
            )
            assert entity_count == 0

            # Verify association deleted
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 0

    async def test_purger_returns_none_for_nonexistent_row(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test that purger returns None when row doesn't exist."""
        nonexistent_uuid = uuid.uuid4()

        async with database_connection.begin_session_read_committed() as db_sess:
            spec = SimpleRBACEntityPurgerSpec(entity_uuid=nonexistent_uuid)
            purger: RBACEntityPurger[RBACEntityPurgerTestRow] = RBACEntityPurger(
                row_class=RBACEntityPurgerTestRow,
                pk_value=nonexistent_uuid,
                spec=spec,
            )
            result = await execute_rbac_entity_purger(db_sess, purger)
            assert result is None


class TestRBACEntityPurgerWithPermissions:
    """Tests for entity purger with permissions cleanup."""

    @pytest.fixture
    async def entity_with_permissions(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[EntityWithPermissionsContext, None]:
        """Create entity with role and permissions (entity-as-scope pattern)."""
        user_id = str(uuid.uuid4())
        entity_uuid = uuid.uuid4()
        role_id: UUID

        async with database_connection.begin_session_read_committed() as db_sess:
            entity_row = RBACEntityPurgerTestRow(
                id=entity_uuid,
                name="test-entity",
                owner_scope_type=ScopeType.USER.value,
                owner_scope_id=user_id,
            )
            db_sess.add(entity_row)

            assoc_row = AssociationScopesEntitiesRow(
                scope_type=ScopeType.USER,
                scope_id=user_id,
                entity_type=EntityType.VFOLDER,
                entity_id=str(entity_uuid),
            )
            db_sess.add(assoc_row)

            role = RoleRow(
                id=uuid.uuid4(),
                name="system-role",
                source=RoleSource.SYSTEM,
            )
            db_sess.add(role)
            await db_sess.flush()

            # Create permissions where the entity is the scope
            for op in [OperationType.READ, OperationType.UPDATE]:
                perm = PermissionRow(
                    role_id=role.id,
                    scope_type=ScopeType.VFOLDER,
                    scope_id=str(entity_uuid),
                    entity_type=EntityType.VFOLDER,
                    operation=op,
                )
                db_sess.add(perm)
            await db_sess.flush()

            role_id = role.id

        yield EntityWithPermissionsContext(
            entity_uuid=entity_uuid,
            user_id=user_id,
            role_id=role_id,
        )

    @pytest.fixture
    async def two_entities_with_permissions(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[TwoEntitiesContext, None]:
        """Create two entities with shared role and separate permissions."""
        user_id = str(uuid.uuid4())
        entity_uuid1 = uuid.uuid4()
        entity_uuid2 = uuid.uuid4()
        role_id: UUID

        async with database_connection.begin_session_read_committed() as db_sess:
            for entity_uuid, name in [(entity_uuid1, "entity-1"), (entity_uuid2, "entity-2")]:
                entity_row = RBACEntityPurgerTestRow(
                    id=entity_uuid,
                    name=name,
                    owner_scope_type=ScopeType.USER.value,
                    owner_scope_id=user_id,
                )
                db_sess.add(entity_row)

                assoc_row = AssociationScopesEntitiesRow(
                    scope_type=ScopeType.USER,
                    scope_id=user_id,
                    entity_type=EntityType.VFOLDER,
                    entity_id=str(entity_uuid),
                )
                db_sess.add(assoc_row)

            role = RoleRow(
                id=uuid.uuid4(),
                name="system-role",
                source=RoleSource.SYSTEM,
            )
            db_sess.add(role)
            await db_sess.flush()

            for entity_uuid in [entity_uuid1, entity_uuid2]:
                perm = PermissionRow(
                    role_id=role.id,
                    scope_type=ScopeType.VFOLDER,
                    scope_id=str(entity_uuid),
                    entity_type=EntityType.VFOLDER,
                    operation=OperationType.READ,
                )
                db_sess.add(perm)
            await db_sess.flush()

            role_id = role.id

        yield TwoEntitiesContext(
            entity_uuid1=entity_uuid1,
            entity_uuid2=entity_uuid2,
            user_id=user_id,
            role_id=role_id,
        )

    async def test_purger_deletes_entity_scope_permissions(
        self,
        database_connection: ExtendedAsyncSAEngine,
        entity_with_permissions: EntityWithPermissionsContext,
    ) -> None:
        """Test that purger deletes permissions where entity is the scope."""
        ctx = entity_with_permissions

        async with database_connection.begin_session_read_committed() as db_sess:
            spec = SimpleRBACEntityPurgerSpec(entity_uuid=ctx.entity_uuid)
            purger: RBACEntityPurger[RBACEntityPurgerTestRow] = RBACEntityPurger(
                row_class=RBACEntityPurgerTestRow,
                pk_value=ctx.entity_uuid,
                spec=spec,
            )
            await execute_rbac_entity_purger(db_sess, purger)

            # Verify permissions deleted
            perm_count = await db_sess.scalar(sa.select(sa.func.count()).select_from(PermissionRow))
            assert perm_count == 0

    async def test_purger_preserves_unrelated_permissions(
        self,
        database_connection: ExtendedAsyncSAEngine,
        two_entities_with_permissions: TwoEntitiesContext,
    ) -> None:
        """Test that purger preserves permissions for other entities."""
        ctx = two_entities_with_permissions

        async with database_connection.begin_session_read_committed() as db_sess:
            # Delete only entity1
            spec = SimpleRBACEntityPurgerSpec(entity_uuid=ctx.entity_uuid1)
            purger: RBACEntityPurger[RBACEntityPurgerTestRow] = RBACEntityPurger(
                row_class=RBACEntityPurgerTestRow,
                pk_value=ctx.entity_uuid1,
                spec=spec,
            )
            await execute_rbac_entity_purger(db_sess, purger)

            # Verify only entity1's permissions deleted
            perm_count = await db_sess.scalar(sa.select(sa.func.count()).select_from(PermissionRow))
            assert perm_count == 1

            # Verify entity2's permission preserved
            remaining_perm = await db_sess.scalar(sa.select(PermissionRow))
            assert remaining_perm is not None
            assert remaining_perm.scope_id == str(ctx.entity_uuid2)


class TestRBACEntityPurgerMultipleScopes:
    """Tests for entity purger with entities shared across multiple scopes."""

    @pytest.fixture
    async def multi_scope_entity(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[MultiScopeEntityContext, None]:
        """Create entity shared across multiple scopes."""
        owner_user_id = str(uuid.uuid4())
        shared_user_id = str(uuid.uuid4())
        entity_uuid = uuid.uuid4()

        async with database_connection.begin_session_read_committed() as db_sess:
            entity_row = RBACEntityPurgerTestRow(
                id=entity_uuid,
                name="shared-entity",
                owner_scope_type=ScopeType.USER.value,
                owner_scope_id=owner_user_id,
            )
            db_sess.add(entity_row)

            # Create associations for both owner and shared user
            for user_id in [owner_user_id, shared_user_id]:
                assoc_row = AssociationScopesEntitiesRow(
                    scope_type=ScopeType.USER,
                    scope_id=user_id,
                    entity_type=EntityType.VFOLDER,
                    entity_id=str(entity_uuid),
                )
                db_sess.add(assoc_row)
            await db_sess.flush()

        yield MultiScopeEntityContext(
            entity_uuid=entity_uuid,
            owner_user_id=owner_user_id,
            shared_user_id=shared_user_id,
        )

    async def test_purger_deletes_all_scope_associations(
        self,
        database_connection: ExtendedAsyncSAEngine,
        multi_scope_entity: MultiScopeEntityContext,
    ) -> None:
        """Test that purger deletes associations across all scopes."""
        ctx = multi_scope_entity

        async with database_connection.begin_session_read_committed() as db_sess:
            spec = SimpleRBACEntityPurgerSpec(entity_uuid=ctx.entity_uuid)
            purger: RBACEntityPurger[RBACEntityPurgerTestRow] = RBACEntityPurger(
                row_class=RBACEntityPurgerTestRow,
                pk_value=ctx.entity_uuid,
                spec=spec,
            )
            await execute_rbac_entity_purger(db_sess, purger)

            # Verify all associations deleted
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 0


class TestRBACEntityPurgerBidirectionalCleanup:
    """Tests for bidirectional scope association cleanup during entity purging."""

    @pytest.fixture
    async def entity_with_scope_associations(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[EntityWithScopeAssociationsContext, None]:
        """Create entity that acts as a scope for child entities."""
        user_id = str(uuid.uuid4())
        entity_uuid = uuid.uuid4()
        child_entity_ids = [str(uuid.uuid4()) for _ in range(3)]

        async with database_connection.begin_session_read_committed() as db_sess:
            entity_row = RBACEntityPurgerTestRow(
                id=entity_uuid,
                name="parent-entity",
                owner_scope_type=ScopeType.USER.value,
                owner_scope_id=user_id,
            )
            db_sess.add(entity_row)

            # Association where this entity is the target (entity direction)
            assoc_as_entity = AssociationScopesEntitiesRow(
                scope_type=ScopeType.USER,
                scope_id=user_id,
                entity_type=EntityType.VFOLDER,
                entity_id=str(entity_uuid),
            )
            db_sess.add(assoc_as_entity)

            # Associations where this entity is the scope (scope direction)
            for child_id in child_entity_ids:
                assoc_as_scope = AssociationScopesEntitiesRow(
                    scope_type=ScopeType.VFOLDER,
                    scope_id=str(entity_uuid),
                    entity_type=EntityType.SESSION,
                    entity_id=child_id,
                )
                db_sess.add(assoc_as_scope)
            await db_sess.flush()

        yield EntityWithScopeAssociationsContext(
            entity_uuid=entity_uuid,
            user_id=user_id,
            child_entity_ids=child_entity_ids,
        )

    async def test_purger_deletes_scope_associations_in_both_directions(
        self,
        database_connection: ExtendedAsyncSAEngine,
        entity_with_scope_associations: EntityWithScopeAssociationsContext,
    ) -> None:
        """Test that purger deletes associations where entity is both target and scope."""
        ctx = entity_with_scope_associations

        async with database_connection.begin_session_read_committed() as db_sess:
            # Verify initial state: 1 as entity target + 3 as scope = 4 total
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 4

            spec = SimpleRBACEntityPurgerSpec(entity_uuid=ctx.entity_uuid)
            purger: RBACEntityPurger[RBACEntityPurgerTestRow] = RBACEntityPurger(
                row_class=RBACEntityPurgerTestRow,
                pk_value=ctx.entity_uuid,
                spec=spec,
            )
            await execute_rbac_entity_purger(db_sess, purger)

            # Verify all associations deleted (both directions)
            remaining_assocs = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert remaining_assocs == 0

    async def test_purger_preserves_unrelated_scope_associations(
        self,
        database_connection: ExtendedAsyncSAEngine,
        entity_with_scope_associations: EntityWithScopeAssociationsContext,
    ) -> None:
        """Test that purger preserves associations for unrelated scopes."""
        ctx = entity_with_scope_associations

        async with database_connection.begin_session_read_committed() as db_sess:
            # Add an unrelated association (different scope)
            unrelated_scope_id = str(uuid.uuid4())
            unrelated_assoc = AssociationScopesEntitiesRow(
                scope_type=ScopeType.USER,
                scope_id=unrelated_scope_id,
                entity_type=EntityType.SESSION,
                entity_id=str(uuid.uuid4()),
            )
            db_sess.add(unrelated_assoc)
            await db_sess.flush()

            spec = SimpleRBACEntityPurgerSpec(entity_uuid=ctx.entity_uuid)
            purger: RBACEntityPurger[RBACEntityPurgerTestRow] = RBACEntityPurger(
                row_class=RBACEntityPurgerTestRow,
                pk_value=ctx.entity_uuid,
                spec=spec,
            )
            await execute_rbac_entity_purger(db_sess, purger)

            # Verify unrelated association preserved
            remaining_assocs = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert remaining_assocs == 1


# =============================================================================
# Batch Purger Tests
# =============================================================================


class TestEntityBatchPurgerSpec(RBACEntityBatchPurgerSpec[RBACEntityPurgerTestRow]):
    """Test spec for batch purging entities."""

    def build_subquery(self) -> sa.sql.Select[tuple[RBACEntityPurgerTestRow]]:
        return sa.select(RBACEntityPurgerTestRow)

    def entity_type(self) -> EntityType:
        return EntityType.VFOLDER

    def scope_type(self) -> ScopeType:
        return ScopeType.VFOLDER


class TestRBACEntityBatchPurger:
    """Tests for RBAC entity batch purger operations."""

    @pytest.fixture
    async def batch_entities(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[BatchEntitiesContext, None]:
        """Create multiple entities with scope associations."""
        user_id = str(uuid.uuid4())
        entity_uuids = [uuid.uuid4() for _ in range(5)]

        async with database_connection.begin_session_read_committed() as db_sess:
            for i, entity_uuid in enumerate(entity_uuids):
                entity_row = RBACEntityPurgerTestRow(
                    id=entity_uuid,
                    name=f"entity-{i}",
                    owner_scope_type=ScopeType.USER.value,
                    owner_scope_id=user_id,
                )
                db_sess.add(entity_row)

                assoc_row = AssociationScopesEntitiesRow(
                    scope_type=ScopeType.USER,
                    scope_id=user_id,
                    entity_type=EntityType.VFOLDER,
                    entity_id=str(entity_uuid),
                )
                db_sess.add(assoc_row)
            await db_sess.flush()

        yield BatchEntitiesContext(
            entity_uuids=entity_uuids,
            user_id=user_id,
        )

    @pytest.fixture
    async def batch_entities_with_permissions(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[BatchEntitiesWithPermissionsContext, None]:
        """Create multiple entities with shared role and permissions."""
        user_id = str(uuid.uuid4())
        entity_uuids = [uuid.uuid4() for _ in range(3)]
        role_id: UUID

        async with database_connection.begin_session_read_committed() as db_sess:
            for i, entity_uuid in enumerate(entity_uuids):
                entity_row = RBACEntityPurgerTestRow(
                    id=entity_uuid,
                    name=f"entity-{i}",
                    owner_scope_type=ScopeType.USER.value,
                    owner_scope_id=user_id,
                )
                db_sess.add(entity_row)

                assoc_row = AssociationScopesEntitiesRow(
                    scope_type=ScopeType.USER,
                    scope_id=user_id,
                    entity_type=EntityType.VFOLDER,
                    entity_id=str(entity_uuid),
                )
                db_sess.add(assoc_row)

            # Create role
            role = RoleRow(
                id=uuid.uuid4(),
                name="batch-test-role",
                source=RoleSource.SYSTEM,
            )
            db_sess.add(role)
            await db_sess.flush()

            # Create permissions where entities are the scope
            for entity_uuid in entity_uuids:
                perm = PermissionRow(
                    role_id=role.id,
                    scope_type=ScopeType.VFOLDER,
                    scope_id=str(entity_uuid),
                    entity_type=EntityType.VFOLDER,
                    operation=OperationType.READ,
                )
                db_sess.add(perm)
            await db_sess.flush()

            role_id = role.id

        yield BatchEntitiesWithPermissionsContext(
            entity_uuids=entity_uuids,
            user_id=user_id,
            role_id=role_id,
        )

    async def test_batch_purger_deletes_multiple_entities(
        self,
        database_connection: ExtendedAsyncSAEngine,
        batch_entities: BatchEntitiesContext,
    ) -> None:
        """Test that batch purger deletes all entities and their associations."""

        async with database_connection.begin_session_read_committed() as db_sess:
            # Verify initial state
            entity_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACEntityPurgerTestRow)
            )
            assert entity_count == 5

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 5

            # Execute batch purge
            spec = TestEntityBatchPurgerSpec()
            purger: RBACEntityBatchPurger[RBACEntityPurgerTestRow] = RBACEntityBatchPurger(
                spec=spec
            )
            result = await execute_rbac_entity_batch_purger(db_sess, purger)

            # Verify result
            assert isinstance(result, RBACEntityBatchPurgerResult)
            assert result.deleted_count == 5
            assert result.deleted_scope_association_count == 5
            assert result.deleted_permission_count == 0

            # Verify all entities deleted
            remaining_entities = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACEntityPurgerTestRow)
            )
            assert remaining_entities == 0

            # Verify all associations deleted
            remaining_assocs = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert remaining_assocs == 0

    async def test_batch_purger_cleans_permissions(
        self,
        database_connection: ExtendedAsyncSAEngine,
        batch_entities_with_permissions: BatchEntitiesWithPermissionsContext,
    ) -> None:
        """Test that batch purger cleans up permissions."""

        async with database_connection.begin_session_read_committed() as db_sess:
            # Verify initial state
            perm_count = await db_sess.scalar(sa.select(sa.func.count()).select_from(PermissionRow))
            assert perm_count == 3

            # Execute batch purge
            spec = TestEntityBatchPurgerSpec()
            purger: RBACEntityBatchPurger[RBACEntityPurgerTestRow] = RBACEntityBatchPurger(
                spec=spec
            )
            result = await execute_rbac_entity_batch_purger(db_sess, purger)

            # Verify result
            assert result.deleted_count == 3
            assert result.deleted_permission_count == 3
            assert result.deleted_scope_association_count == 3

            # Verify permissions deleted
            remaining_perms = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(PermissionRow)
            )
            assert remaining_perms == 0

    async def test_batch_purger_handles_empty_batch(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test that batch purger handles empty results gracefully."""
        async with database_connection.begin_session_read_committed() as db_sess:
            spec = TestEntityBatchPurgerSpec()
            purger: RBACEntityBatchPurger[RBACEntityPurgerTestRow] = RBACEntityBatchPurger(
                spec=spec
            )
            result = await execute_rbac_entity_batch_purger(db_sess, purger)

            assert isinstance(result, RBACEntityBatchPurgerResult)
            assert result.deleted_count == 0
            assert result.deleted_permission_count == 0
            assert result.deleted_scope_association_count == 0

    async def test_batch_purger_respects_batch_size(
        self,
        database_connection: ExtendedAsyncSAEngine,
        batch_entities: BatchEntitiesContext,
    ) -> None:
        """Test that batch purger processes in batches according to batch_size."""

        async with database_connection.begin_session_read_committed() as db_sess:
            # Execute batch purge with small batch size
            spec = TestEntityBatchPurgerSpec()
            purger: RBACEntityBatchPurger[RBACEntityPurgerTestRow] = RBACEntityBatchPurger(
                spec=spec,
                batch_size=2,  # Small batch size to force multiple iterations
            )
            result = await execute_rbac_entity_batch_purger(db_sess, purger)

            # Should still delete all 5 entities across multiple batches
            assert result.deleted_count == 5
            assert result.deleted_scope_association_count == 5

            # Verify all entities deleted
            remaining_entities = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACEntityPurgerTestRow)
            )
            assert remaining_entities == 0


# =============================================================================
# Composite Primary Key Tests
# =============================================================================


class CompositePKPurgerTestRow(Base):  # type: ignore[misc]
    """ORM model with composite primary key for testing rejection."""

    __tablename__ = "test_rbac_purger_composite_pk"
    __table_args__ = {"extend_existing": True}

    tenant_id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)


class CompositePKPurgerSpec(RBACEntityPurgerSpec):
    """Purger spec for composite PK testing."""

    def __init__(self, entity_uuid: str) -> None:
        self._entity_uuid = entity_uuid

    def entity(self) -> RBACEntity:
        return RBACEntity(
            entity=ObjectId(entity_type=EntityType.VFOLDER, entity_id=self._entity_uuid)
        )

    def scope_type(self) -> ScopeType:
        return ScopeType.VFOLDER


class CompositePKBatchPurgerSpec(RBACEntityBatchPurgerSpec[CompositePKPurgerTestRow]):
    """Batch purger spec for composite PK testing."""

    def build_subquery(self) -> sa.Select[Any]:
        return sa.select(CompositePKPurgerTestRow)

    def entity_type(self) -> EntityType:
        return EntityType.VFOLDER

    def scope_type(self) -> ScopeType:
        return ScopeType.VFOLDER


class TestRBACEntityPurgerCompositePK:
    """Tests for composite primary key rejection in RBAC entity purger."""

    async def test_single_purger_rejects_composite_pk(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> None:
        """Test that single entity purger rejects composite PK tables."""
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: CompositePKPurgerTestRow.__table__.create(c, checkfirst=True)
            )

        try:
            async with database_connection.begin_session_read_committed() as db_sess:
                spec = CompositePKPurgerSpec(entity_uuid="test-123")
                purger = RBACEntityPurger(
                    row_class=CompositePKPurgerTestRow,
                    pk_value=1,  # PK value (error raised before lookup due to composite PK)
                    spec=spec,
                )

                with pytest.raises(UnsupportedCompositePrimaryKeyError):
                    await execute_rbac_entity_purger(db_sess, purger)
        finally:
            async with database_connection.begin() as conn:
                await conn.run_sync(
                    lambda c: CompositePKPurgerTestRow.__table__.drop(c, checkfirst=True)
                )

    async def test_batch_purger_rejects_composite_pk(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> None:
        """Test that batch entity purger rejects composite PK tables."""
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: CompositePKPurgerTestRow.__table__.create(c, checkfirst=True)
            )

        try:
            async with database_connection.begin_session_read_committed() as db_sess:
                spec = CompositePKBatchPurgerSpec()
                purger = RBACEntityBatchPurger(spec=spec)

                with pytest.raises(UnsupportedCompositePrimaryKeyError):
                    await execute_rbac_entity_batch_purger(db_sess, purger)
        finally:
            async with database_connection.begin() as conn:
                await conn.run_sync(
                    lambda c: CompositePKPurgerTestRow.__table__.drop(c, checkfirst=True)
                )
