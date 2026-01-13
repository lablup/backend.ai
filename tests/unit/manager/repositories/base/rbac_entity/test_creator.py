"""Integration tests for RBAC entity creator with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.types import EntityType, ScopeType
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.entity_field import EntityFieldRow
from ai.backend.manager.repositories.base.rbac_entity.creator import (
    RBACCreator,
    RBACCreatorResult,
    RBACCreatorSpec,
    execute_rbac_creator,
)
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


# =============================================================================
# Test Row Models
# =============================================================================


class RBACCreatorTestRow(Base):
    """ORM model implementing RBACEntityRow for creator testing."""

    __tablename__ = "test_rbac_creator"
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

    def field_id(self) -> ObjectId | None:
        return None


class RBACFieldCreatorTestRow(Base):
    """ORM model for field-scoped entity testing."""

    __tablename__ = "test_rbac_field_creator"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(
        GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    owner_scope_type: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    owner_scope_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    parent_entity_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)

    def scope_id(self) -> ScopeId:
        return ScopeId(scope_type=ScopeType(self.owner_scope_type), scope_id=self.owner_scope_id)

    def entity_id(self) -> ObjectId:
        return ObjectId(entity_type=EntityType.VFOLDER, entity_id=self.parent_entity_id)

    def field_id(self) -> ObjectId:
        return ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(self.id))


# =============================================================================
# Creator Spec Implementations
# =============================================================================


class SimpleRBACCreatorSpec(RBACCreatorSpec[RBACCreatorTestRow]):
    """Simple creator spec for entity testing."""

    def __init__(
        self,
        name: str,
        scope_type: ScopeType,
        scope_id: str,
        entity_id: UUID | None = None,
    ) -> None:
        self._name = name
        self._scope_type = scope_type
        self._scope_id = scope_id
        self._entity_id = entity_id or uuid.uuid4()

    def build_row(self) -> RBACCreatorTestRow:
        return RBACCreatorTestRow(
            id=self._entity_id,
            name=self._name,
            owner_scope_type=self._scope_type.value,
            owner_scope_id=self._scope_id,
        )


class SimpleRBACFieldCreatorSpec(RBACCreatorSpec[RBACFieldCreatorTestRow]):
    """Simple creator spec for field-scoped entity testing."""

    def __init__(
        self,
        name: str,
        scope_type: ScopeType,
        scope_id: str,
        parent_entity_id: str,
        field_id: UUID | None = None,
    ) -> None:
        self._name = name
        self._scope_type = scope_type
        self._scope_id = scope_id
        self._parent_entity_id = parent_entity_id
        self._field_id = field_id or uuid.uuid4()

    def build_row(self) -> RBACFieldCreatorTestRow:
        return RBACFieldCreatorTestRow(
            id=self._field_id,
            name=self._name,
            owner_scope_type=self._scope_type.value,
            owner_scope_id=self._scope_id,
            parent_entity_id=self._parent_entity_id,
        )


# =============================================================================
# Tables List
# =============================================================================

CREATOR_TABLES = [
    RBACCreatorTestRow,
    RBACFieldCreatorTestRow,
    AssociationScopesEntitiesRow,
    EntityFieldRow,
]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def create_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    """Create RBAC creator test tables."""
    async with with_tables(database_connection, CREATOR_TABLES):  # type: ignore[arg-type]
        yield


# =============================================================================
# Tests
# =============================================================================


class TestRBACCreatorBasic:
    """Basic tests for RBAC entity creator operations."""

    async def test_create_entity_inserts_row_and_association(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test creating an entity inserts both main row and scope association."""
        user_id = str(uuid.uuid4())

        async with database_connection.begin_session() as db_sess:
            # Create entity
            spec = SimpleRBACCreatorSpec(
                name="test-entity",
                scope_type=ScopeType.USER,
                scope_id=user_id,
            )
            creator: RBACCreator[RBACCreatorTestRow] = RBACCreator(spec=spec)
            result = await execute_rbac_creator(db_sess, creator)

            # Verify result
            assert isinstance(result, RBACCreatorResult)
            assert result.row.name == "test-entity"
            assert result.row.id is not None

            # Verify main row was inserted
            entity_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACCreatorTestRow)
            )
            assert entity_count == 1

            # Verify association was created
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 1

            # Verify association details
            assoc_row = await db_sess.scalar(sa.select(AssociationScopesEntitiesRow))
            assert assoc_row is not None
            assert assoc_row.scope_type == ScopeType.USER
            assert assoc_row.scope_id == user_id
            assert assoc_row.entity_type == EntityType.VFOLDER
            assert assoc_row.entity_id == str(result.row.id)

    async def test_create_entity_with_project_scope(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test creating an entity with project scope."""
        project_id = str(uuid.uuid4())

        async with database_connection.begin_session() as db_sess:
            spec = SimpleRBACCreatorSpec(
                name="project-entity",
                scope_type=ScopeType.PROJECT,
                scope_id=project_id,
            )
            creator: RBACCreator[RBACCreatorTestRow] = RBACCreator(spec=spec)
            await execute_rbac_creator(db_sess, creator)

            # Verify association has correct scope
            assoc_row = await db_sess.scalar(sa.select(AssociationScopesEntitiesRow))
            assert assoc_row is not None
            assert assoc_row.scope_type == ScopeType.PROJECT
            assert assoc_row.scope_id == project_id

    async def test_create_multiple_entities_sequentially(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test creating multiple entities in sequence."""
        user_id = str(uuid.uuid4())

        async with database_connection.begin_session() as db_sess:
            for i in range(5):
                spec = SimpleRBACCreatorSpec(
                    name=f"entity-{i}",
                    scope_type=ScopeType.USER,
                    scope_id=user_id,
                )
                creator: RBACCreator[RBACCreatorTestRow] = RBACCreator(spec=spec)
                result = await execute_rbac_creator(db_sess, creator)
                assert result.row.name == f"entity-{i}"

            # Verify counts
            entity_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACCreatorTestRow)
            )
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert entity_count == 5
            assert assoc_count == 5


class TestRBACCreatorFieldScoped:
    """Tests for field-scoped entity creation."""

    async def test_create_field_entity_inserts_entity_field_row(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test creating a field-scoped entity inserts EntityFieldRow instead of association."""
        user_id = str(uuid.uuid4())
        parent_entity_id = str(uuid.uuid4())

        async with database_connection.begin_session() as db_sess:
            # Create field entity
            spec = SimpleRBACFieldCreatorSpec(
                name="test-field",
                scope_type=ScopeType.USER,
                scope_id=user_id,
                parent_entity_id=parent_entity_id,
            )
            creator: RBACCreator[RBACFieldCreatorTestRow] = RBACCreator(spec=spec)
            result = await execute_rbac_creator(db_sess, creator)

            # Verify result
            assert isinstance(result, RBACCreatorResult)
            assert result.row.name == "test-field"

            # Verify EntityFieldRow was created (not AssociationScopesEntitiesRow)
            field_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(EntityFieldRow)
            )
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert field_count == 1
            assert assoc_count == 0

            # Verify EntityFieldRow details
            field_row = await db_sess.scalar(sa.select(EntityFieldRow))
            assert field_row is not None
            assert field_row.entity_type == EntityType.VFOLDER.value
            assert field_row.entity_id == parent_entity_id
            assert field_row.field_type == EntityType.VFOLDER.value
            assert field_row.field_id == str(result.row.id)

    async def test_create_multiple_fields_for_same_entity(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test creating multiple fields for the same parent entity."""
        user_id = str(uuid.uuid4())
        parent_entity_id = str(uuid.uuid4())

        async with database_connection.begin_session() as db_sess:
            for i in range(3):
                spec = SimpleRBACFieldCreatorSpec(
                    name=f"field-{i}",
                    scope_type=ScopeType.USER,
                    scope_id=user_id,
                    parent_entity_id=parent_entity_id,
                )
                creator: RBACCreator[RBACFieldCreatorTestRow] = RBACCreator(spec=spec)
                await execute_rbac_creator(db_sess, creator)

            # Verify counts
            entity_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACFieldCreatorTestRow)
            )
            field_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(EntityFieldRow)
            )
            assert entity_count == 3
            assert field_count == 3


class TestRBACCreatorIdempotent:
    """Tests for idempotent behavior of RBAC entity creator."""

    async def test_creator_handles_duplicate_association_gracefully(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test that creating entity with existing association doesn't fail.

        The creator uses insert_on_conflict_do_nothing, so duplicate associations
        should be handled gracefully without errors.
        """
        user_id = str(uuid.uuid4())
        entity_id = uuid.uuid4()

        async with database_connection.begin_session() as db_sess:
            # First creation
            spec1 = SimpleRBACCreatorSpec(
                name="test-entity",
                scope_type=ScopeType.USER,
                scope_id=user_id,
                entity_id=entity_id,
            )
            creator1: RBACCreator[RBACCreatorTestRow] = RBACCreator(spec=spec1)
            result1 = await execute_rbac_creator(db_sess, creator1)
            assert result1.row.id == entity_id

            # Verify one association created
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 1

        async with database_connection.begin_session() as db_sess:
            # Manually create another entity row with same ID (simulating re-creation)
            # but the association already exists
            new_entity_row = RBACCreatorTestRow(
                id=uuid.uuid4(),  # Different entity
                name="another-entity",
                owner_scope_type=ScopeType.USER.value,
                owner_scope_id=user_id,
            )
            db_sess.add(new_entity_row)
            await db_sess.flush()

            # Manually try to insert duplicate association (same scope, same entity_id)
            # This simulates what would happen if somehow the same entity is created twice
            from ai.backend.manager.repositories.base.rbac_entity.utils import (
                insert_on_conflict_do_nothing,
            )

            duplicate_assoc = AssociationScopesEntitiesRow(
                scope_type=ScopeType.USER,
                scope_id=user_id,
                entity_type=EntityType.VFOLDER,
                entity_id=str(entity_id),  # Same entity_id as first
            )
            # Should not raise an error
            await insert_on_conflict_do_nothing(db_sess, duplicate_assoc)

            # Verify still only one association (no duplicate)
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 1

    async def test_creator_handles_duplicate_entity_field_gracefully(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test that creating field entity with existing EntityFieldRow doesn't fail."""
        user_id = str(uuid.uuid4())
        parent_entity_id = str(uuid.uuid4())
        field_id = uuid.uuid4()

        async with database_connection.begin_session() as db_sess:
            # First creation
            spec = SimpleRBACFieldCreatorSpec(
                name="test-field",
                scope_type=ScopeType.USER,
                scope_id=user_id,
                parent_entity_id=parent_entity_id,
                field_id=field_id,
            )
            creator: RBACCreator[RBACFieldCreatorTestRow] = RBACCreator(spec=spec)
            await execute_rbac_creator(db_sess, creator)

            # Verify one EntityFieldRow created
            field_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(EntityFieldRow)
            )
            assert field_count == 1

        async with database_connection.begin_session() as db_sess:
            # Try to insert duplicate EntityFieldRow
            from ai.backend.manager.repositories.base.rbac_entity.utils import (
                insert_on_conflict_do_nothing,
            )

            duplicate_field = EntityFieldRow(
                entity_type=EntityType.VFOLDER.value,
                entity_id=parent_entity_id,
                field_type=EntityType.VFOLDER.value,
                field_id=str(field_id),  # Same field_id as first
            )
            # Should not raise an error
            await insert_on_conflict_do_nothing(db_sess, duplicate_field)

            # Verify still only one EntityFieldRow (no duplicate)
            field_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(EntityFieldRow)
            )
            assert field_count == 1
