"""Integration tests for RBAC field creator with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.data.permission.id import FieldRef, ObjectId
from ai.backend.manager.data.permission.types import EntityType, FieldType, ScopeType
from ai.backend.manager.errors.repository import UnsupportedCompositePrimaryKeyError
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.rbac_models.entity_field import EntityFieldRow
from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.repositories.base.rbac.field_creator import (
    RBACBulkFieldCreator,
    RBACBulkFieldCreatorResult,
    RBACFieldCreator,
    RBACFieldCreatorResult,
    execute_rbac_bulk_field_creator,
    execute_rbac_field_creator,
)
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


# =============================================================================
# Test Row Models
# =============================================================================


class RBACFieldCreatorTestRow(Base):
    """ORM model implementing RBACFieldRow protocol for field creator testing."""

    __tablename__ = "test_rbac_field_creator"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(
        GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    owner_scope_type: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    owner_scope_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    parent_entity_type: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    _parent_entity_id: Mapped[str] = mapped_column(
        "parent_entity_id", sa.String(64), nullable=False
    )

    def parent_entity_id(self) -> ObjectId:
        return ObjectId(
            entity_type=EntityType(self.parent_entity_type), entity_id=self._parent_entity_id
        )

    def field_ref(self) -> FieldRef:
        return FieldRef(field_type=FieldType.KERNEL, field_id=str(self.id))


# =============================================================================
# Creator Spec Implementations
# =============================================================================


class SimpleFieldCreatorSpec(CreatorSpec[RBACFieldCreatorTestRow]):
    """Simple creator spec for field testing."""

    def __init__(
        self,
        name: str,
        scope_type: ScopeType,
        scope_id: str,
        parent_entity_id: str,
        parent_entity_type: EntityType = EntityType.VFOLDER,
        field_id: UUID | None = None,
    ) -> None:
        self._name = name
        self._scope_type = scope_type
        self._scope_id = scope_id
        self._parent_entity_id = parent_entity_id
        self._parent_entity_type = parent_entity_type
        self._field_id = field_id

    def build_row(self) -> RBACFieldCreatorTestRow:
        row_kwargs: dict = {
            "name": self._name,
            "owner_scope_type": self._scope_type.value,
            "owner_scope_id": self._scope_id,
            "parent_entity_type": self._parent_entity_type.value,
            "_parent_entity_id": self._parent_entity_id,
        }
        if self._field_id is not None:
            row_kwargs["id"] = self._field_id
        return RBACFieldCreatorTestRow(**row_kwargs)


# =============================================================================
# Tables List
# =============================================================================

FIELD_CREATOR_TABLES = [
    RBACFieldCreatorTestRow,
    EntityFieldRow,
]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def create_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    """Create RBAC field creator test tables."""
    async with with_tables(database_connection, FIELD_CREATOR_TABLES):  # type: ignore[arg-type]
        yield


# =============================================================================
# Single Field Creator Tests
# =============================================================================


class TestRBACFieldCreatorBasic:
    """Basic tests for RBAC field creator operations."""

    async def test_create_field_inserts_row_and_entity_field(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test creating a field inserts both main row and entity-field mapping."""
        user_id = str(uuid.uuid4())
        parent_entity_id = str(uuid.uuid4())

        async with database_connection.begin_session() as db_sess:
            # Create field
            spec = SimpleFieldCreatorSpec(
                name="test-field",
                scope_type=ScopeType.USER,
                scope_id=user_id,
                parent_entity_id=parent_entity_id,
            )
            creator: RBACFieldCreator[RBACFieldCreatorTestRow] = RBACFieldCreator(
                spec=spec,
                entity_type=EntityType.VFOLDER,
                entity_id=parent_entity_id,
                field_type=FieldType.KERNEL,
            )
            result = await execute_rbac_field_creator(db_sess, creator)

            # Verify result
            assert isinstance(result, RBACFieldCreatorResult)
            assert result.row.name == "test-field"
            assert result.row.id is not None

            # Verify main row was inserted
            field_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACFieldCreatorTestRow)
            )
            assert field_count == 1

            # Verify EntityFieldRow was created
            entity_field_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(EntityFieldRow)
            )
            assert entity_field_count == 1

            # Verify EntityFieldRow details
            entity_field_row = await db_sess.scalar(sa.select(EntityFieldRow))
            assert entity_field_row is not None
            assert entity_field_row.entity_type == EntityType.VFOLDER.value
            assert entity_field_row.entity_id == parent_entity_id
            assert entity_field_row.field_type == FieldType.KERNEL.value
            assert entity_field_row.field_id == str(result.row.id)

    async def test_create_multiple_fields_for_same_parent(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test creating multiple fields for the same parent entity."""
        user_id = str(uuid.uuid4())
        parent_entity_id = str(uuid.uuid4())

        async with database_connection.begin_session() as db_sess:
            for i in range(3):
                spec = SimpleFieldCreatorSpec(
                    name=f"field-{i}",
                    scope_type=ScopeType.USER,
                    scope_id=user_id,
                    parent_entity_id=parent_entity_id,
                )
                creator: RBACFieldCreator[RBACFieldCreatorTestRow] = RBACFieldCreator(
                    spec=spec,
                    entity_type=EntityType.VFOLDER,
                    entity_id=parent_entity_id,
                    field_type=FieldType.KERNEL,
                )
                await execute_rbac_field_creator(db_sess, creator)

            # Verify counts
            field_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACFieldCreatorTestRow)
            )
            entity_field_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(EntityFieldRow)
            )
            assert field_count == 3
            assert entity_field_count == 3


class TestRBACFieldCreatorIdempotent:
    """Tests for idempotent behavior of RBAC field creator."""

    async def test_creator_handles_duplicate_entity_field_gracefully(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test that creating field with existing EntityFieldRow doesn't fail."""
        user_id = str(uuid.uuid4())
        parent_entity_id = str(uuid.uuid4())
        field_id = uuid.uuid4()

        async with database_connection.begin_session() as db_sess:
            # First creation
            spec = SimpleFieldCreatorSpec(
                name="test-field",
                scope_type=ScopeType.USER,
                scope_id=user_id,
                parent_entity_id=parent_entity_id,
                field_id=field_id,
            )
            creator: RBACFieldCreator[RBACFieldCreatorTestRow] = RBACFieldCreator(
                spec=spec,
                entity_type=EntityType.VFOLDER,
                entity_id=parent_entity_id,
                field_type=FieldType.KERNEL,
            )
            await execute_rbac_field_creator(db_sess, creator)

            # Verify one EntityFieldRow created
            entity_field_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(EntityFieldRow)
            )
            assert entity_field_count == 1

        async with database_connection.begin_session() as db_sess:
            # Try to insert duplicate EntityFieldRow
            from ai.backend.manager.repositories.base.rbac.utils import (
                insert_on_conflict_do_nothing,
            )

            duplicate_field = EntityFieldRow(
                entity_type=EntityType.VFOLDER.value,
                entity_id=parent_entity_id,
                field_type=FieldType.KERNEL.value,
                field_id=str(field_id),  # Same field_id as first
            )
            # Should not raise an error
            await insert_on_conflict_do_nothing(db_sess, duplicate_field)

            # Verify still only one EntityFieldRow (no duplicate)
            entity_field_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(EntityFieldRow)
            )
            assert entity_field_count == 1


# =============================================================================
# Bulk Field Creator Tests
# =============================================================================


class TestRBACBulkFieldCreator:
    """Tests for bulk field creator operations."""

    async def test_bulk_create_multiple_fields(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test bulk creating multiple fields."""
        user_id = str(uuid.uuid4())
        parent_entity_id = str(uuid.uuid4())

        async with database_connection.begin_session() as db_sess:
            specs = [
                SimpleFieldCreatorSpec(
                    name=f"field-{i}",
                    scope_type=ScopeType.USER,
                    scope_id=user_id,
                    parent_entity_id=parent_entity_id,
                )
                for i in range(5)
            ]
            creator: RBACBulkFieldCreator[RBACFieldCreatorTestRow] = RBACBulkFieldCreator(
                specs=specs,
                entity_type=EntityType.VFOLDER,
                entity_id=parent_entity_id,
                field_type=FieldType.KERNEL,
            )
            result = await execute_rbac_bulk_field_creator(db_sess, creator)

            # Verify result
            assert isinstance(result, RBACBulkFieldCreatorResult)
            assert len(result.rows) == 5
            for i, row in enumerate(result.rows):
                assert row.name == f"field-{i}"

            # Verify counts
            field_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACFieldCreatorTestRow)
            )
            entity_field_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(EntityFieldRow)
            )
            assert field_count == 5
            assert entity_field_count == 5

    async def test_bulk_create_with_empty_specs(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test bulk creating with empty specs returns empty result."""
        async with database_connection.begin_session() as db_sess:
            creator: RBACBulkFieldCreator[RBACFieldCreatorTestRow] = RBACBulkFieldCreator(
                specs=[],
                entity_type=EntityType.VFOLDER,
                entity_id="dummy",
                field_type=FieldType.KERNEL,
            )
            result = await execute_rbac_bulk_field_creator(db_sess, creator)

            assert isinstance(result, RBACBulkFieldCreatorResult)
            assert len(result.rows) == 0

            # Verify no fields created
            field_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACFieldCreatorTestRow)
            )
            assert field_count == 0

    async def test_bulk_create_same_parent_entity(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test bulk creating fields with same parent entity."""
        user_id = str(uuid.uuid4())
        parent_entity_id = str(uuid.uuid4())

        async with database_connection.begin_session() as db_sess:
            specs = [
                SimpleFieldCreatorSpec(
                    name="field-1",
                    scope_type=ScopeType.USER,
                    scope_id=user_id,
                    parent_entity_id=parent_entity_id,
                ),
                SimpleFieldCreatorSpec(
                    name="field-2",
                    scope_type=ScopeType.USER,
                    scope_id=user_id,
                    parent_entity_id=parent_entity_id,
                ),
            ]
            creator: RBACBulkFieldCreator[RBACFieldCreatorTestRow] = RBACBulkFieldCreator(
                specs=specs,
                entity_type=EntityType.VFOLDER,
                entity_id=parent_entity_id,
                field_type=FieldType.KERNEL,
            )
            result = await execute_rbac_bulk_field_creator(db_sess, creator)

            assert len(result.rows) == 2

            # Verify EntityFieldRows
            entity_field_rows = (await db_sess.scalars(sa.select(EntityFieldRow))).all()
            assert len(entity_field_rows) == 2

            # All should have same parent entity
            for ef in entity_field_rows:
                assert ef.entity_id == parent_entity_id


# =============================================================================
# Composite Primary Key Tests
# =============================================================================


class CompositePKFieldCreatorTestRow(Base):
    """ORM model with composite primary key for testing rejection."""

    __tablename__ = "test_rbac_field_creator_composite_pk"
    __table_args__ = {"extend_existing": True}

    tenant_id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)


class CompositePKFieldCreatorSpec(CreatorSpec[CompositePKFieldCreatorTestRow]):
    """Creator spec for composite PK testing."""

    def __init__(self, tenant_id: int, item_id: int, name: str) -> None:
        self._tenant_id = tenant_id
        self._item_id = item_id
        self._name = name

    def build_row(self) -> CompositePKFieldCreatorTestRow:
        return CompositePKFieldCreatorTestRow(
            tenant_id=self._tenant_id,
            item_id=self._item_id,
            name=self._name,
        )


class TestRBACFieldCreatorCompositePK:
    """Tests for composite primary key rejection in RBAC field creator."""

    async def test_single_creator_rejects_composite_pk(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> None:
        """Test that single field creator rejects composite PK tables."""
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: CompositePKFieldCreatorTestRow.__table__.create(c, checkfirst=True)
            )

        try:
            async with database_connection.begin_session() as db_sess:
                spec = CompositePKFieldCreatorSpec(tenant_id=1, item_id=1, name="test")
                creator = RBACFieldCreator(
                    spec=spec,
                    entity_type=EntityType.VFOLDER,
                    entity_id="parent-123",
                    field_type=FieldType.KERNEL,
                )

                with pytest.raises(UnsupportedCompositePrimaryKeyError):
                    await execute_rbac_field_creator(db_sess, creator)
        finally:
            async with database_connection.begin() as conn:
                await conn.run_sync(
                    lambda c: CompositePKFieldCreatorTestRow.__table__.drop(c, checkfirst=True)
                )

    async def test_bulk_creator_rejects_composite_pk(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> None:
        """Test that bulk field creator rejects composite PK tables."""
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: CompositePKFieldCreatorTestRow.__table__.create(c, checkfirst=True)
            )

        try:
            async with database_connection.begin_session() as db_sess:
                specs = [
                    CompositePKFieldCreatorSpec(tenant_id=1, item_id=i, name=f"test-{i}")
                    for i in range(3)
                ]
                creator = RBACBulkFieldCreator(
                    specs=specs,
                    entity_type=EntityType.VFOLDER,
                    entity_id="parent-123",
                    field_type=FieldType.KERNEL,
                )

                with pytest.raises(UnsupportedCompositePrimaryKeyError):
                    await execute_rbac_bulk_field_creator(db_sess, creator)
        finally:
            async with database_connection.begin() as conn:
                await conn.run_sync(
                    lambda c: CompositePKFieldCreatorTestRow.__table__.drop(c, checkfirst=True)
                )
