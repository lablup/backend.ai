"""Integration tests for RBAC field purger with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.data.permission.id import FieldRef, ScopeId
from ai.backend.manager.data.permission.types import (
    EntityType,
    FieldType,
    ScopeType,
)
from ai.backend.manager.errors.repository import UnsupportedCompositePrimaryKeyError
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.rbac_models.entity_field import EntityFieldRow
from ai.backend.manager.repositories.base.rbac.field_purger import (
    RBACFieldBatchPurger,
    RBACFieldBatchPurgerResult,
    RBACFieldBatchPurgerSpec,
    RBACFieldPurger,
    RBACFieldPurgerResult,
    execute_rbac_field_batch_purger,
    execute_rbac_field_purger,
)
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


# =============================================================================
# Test Row Models
# =============================================================================


class RBACFieldPurgerTestRow(Base):
    """ORM model implementing RBACFieldRowProtocol for field purger testing."""

    __tablename__ = "test_rbac_field_purger"
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

    def field(self) -> FieldRef:
        return FieldRef(field_type=FieldType.KERNEL, field_id=str(self.id))


# =============================================================================
# Tables List
# =============================================================================

FIELD_PURGER_TABLES = [
    RBACFieldPurgerTestRow,
    EntityFieldRow,
]


# =============================================================================
# Data Classes for Fixtures
# =============================================================================


@dataclass
class FieldEntityContext:
    """Context for field-scoped entity."""

    field_uuid: UUID
    parent_entity_id: str
    user_id: str


@dataclass
class TwoFieldsContext:
    """Context with two fields for the same parent entity."""

    field_uuid1: UUID
    field_uuid2: UUID
    parent_entity_id: str
    user_id: str


@dataclass
class BatchFieldsContext:
    """Context with multiple field entities for batch purge testing."""

    field_uuids: list[UUID]
    parent_entity_id: str
    user_id: str


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def create_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    """Create RBAC field purger test tables."""
    async with with_tables(database_connection, FIELD_PURGER_TABLES):  # type: ignore[arg-type]
        yield


# =============================================================================
# Tests
# =============================================================================


class TestRBACFieldPurgerBasic:
    """Basic tests for field purger operations."""

    @pytest.fixture
    async def field_entity(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[FieldEntityContext, None]:
        """Create field-scoped entity with EntityFieldRow."""
        user_id = str(uuid.uuid4())
        parent_entity_id = str(uuid.uuid4())
        field_uuid = uuid.uuid4()

        async with database_connection.begin_session() as db_sess:
            field_row = RBACFieldPurgerTestRow(
                id=field_uuid,
                name="test-field",
                owner_scope_type=ScopeType.USER.value,
                owner_scope_id=user_id,
                parent_entity_id=parent_entity_id,
            )
            db_sess.add(field_row)

            entity_field = EntityFieldRow(
                entity_type=EntityType.SESSION.value,
                entity_id=parent_entity_id,
                field_type=FieldType.KERNEL.value,
                field_id=str(field_uuid),
            )
            db_sess.add(entity_field)
            await db_sess.flush()

        yield FieldEntityContext(
            field_uuid=field_uuid,
            parent_entity_id=parent_entity_id,
            user_id=user_id,
        )

    @pytest.fixture
    async def two_fields(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[TwoFieldsContext, None]:
        """Create two field entities for the same parent."""
        user_id = str(uuid.uuid4())
        parent_entity_id = str(uuid.uuid4())
        field_uuid1 = uuid.uuid4()
        field_uuid2 = uuid.uuid4()

        async with database_connection.begin_session() as db_sess:
            for field_uuid, name in [(field_uuid1, "field-1"), (field_uuid2, "field-2")]:
                field_row = RBACFieldPurgerTestRow(
                    id=field_uuid,
                    name=name,
                    owner_scope_type=ScopeType.USER.value,
                    owner_scope_id=user_id,
                    parent_entity_id=parent_entity_id,
                )
                db_sess.add(field_row)

                entity_field = EntityFieldRow(
                    entity_type=EntityType.SESSION.value,
                    entity_id=parent_entity_id,
                    field_type=FieldType.KERNEL.value,
                    field_id=str(field_uuid),
                )
                db_sess.add(entity_field)
            await db_sess.flush()

        yield TwoFieldsContext(
            field_uuid1=field_uuid1,
            field_uuid2=field_uuid2,
            parent_entity_id=parent_entity_id,
            user_id=user_id,
        )

    async def test_purger_deletes_entity_field_row(
        self,
        database_connection: ExtendedAsyncSAEngine,
        field_entity: FieldEntityContext,
    ) -> None:
        """Test that purger deletes EntityFieldRow for field-scoped entities."""
        ctx = field_entity

        async with database_connection.begin_session() as db_sess:
            purger: RBACFieldPurger[RBACFieldPurgerTestRow] = RBACFieldPurger(
                row_class=RBACFieldPurgerTestRow,
                pk_value=ctx.field_uuid,
                field_type=FieldType.KERNEL,
                field_id=str(ctx.field_uuid),
            )
            result = await execute_rbac_field_purger(db_sess, purger)

            # Verify result
            assert isinstance(result, RBACFieldPurgerResult)
            assert result.row.id == ctx.field_uuid

            # Verify field entity row deleted
            field_entity_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACFieldPurgerTestRow)
            )
            assert field_entity_count == 0

            # Verify EntityFieldRow deleted
            entity_field_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(EntityFieldRow)
            )
            assert entity_field_count == 0

    async def test_purger_field_preserves_other_fields(
        self,
        database_connection: ExtendedAsyncSAEngine,
        two_fields: TwoFieldsContext,
    ) -> None:
        """Test that purging one field preserves other fields of the same entity."""
        ctx = two_fields

        async with database_connection.begin_session() as db_sess:
            # Delete only field1
            purger: RBACFieldPurger[RBACFieldPurgerTestRow] = RBACFieldPurger(
                row_class=RBACFieldPurgerTestRow,
                pk_value=ctx.field_uuid1,
                field_type=FieldType.KERNEL,
                field_id=str(ctx.field_uuid1),
            )
            await execute_rbac_field_purger(db_sess, purger)

            # Verify only field1's EntityFieldRow deleted
            entity_field_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(EntityFieldRow)
            )
            assert entity_field_count == 1

            # Verify field2 preserved
            remaining_field = await db_sess.scalar(sa.select(EntityFieldRow))
            assert remaining_field is not None
            assert remaining_field.field_id == str(ctx.field_uuid2)

    async def test_purger_returns_none_for_nonexistent_row(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test that purger returns None when row doesn't exist."""
        nonexistent_uuid = uuid.uuid4()

        async with database_connection.begin_session() as db_sess:
            purger: RBACFieldPurger[RBACFieldPurgerTestRow] = RBACFieldPurger(
                row_class=RBACFieldPurgerTestRow,
                pk_value=nonexistent_uuid,
                field_type=FieldType.KERNEL,
                field_id=str(nonexistent_uuid),
            )
            result = await execute_rbac_field_purger(db_sess, purger)
            assert result is None


# =============================================================================
# Batch Field Purger Tests
# =============================================================================


class TestFieldBatchPurgerSpec(RBACFieldBatchPurgerSpec[RBACFieldPurgerTestRow]):
    """Test spec for batch purging field-scoped entities."""

    def build_subquery(self) -> sa.sql.Select[tuple[RBACFieldPurgerTestRow]]:
        return sa.select(RBACFieldPurgerTestRow)

    def field_type(self) -> FieldType:
        return FieldType.KERNEL


class TestRBACFieldBatchPurger:
    """Tests for RBAC field batch purger operations."""

    @pytest.fixture
    async def batch_fields(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> AsyncGenerator[BatchFieldsContext, None]:
        """Create multiple field entities with EntityFieldRows."""
        user_id = str(uuid.uuid4())
        parent_entity_id = str(uuid.uuid4())
        field_uuids = [uuid.uuid4() for _ in range(4)]

        async with database_connection.begin_session() as db_sess:
            for i, field_uuid in enumerate(field_uuids):
                field_row = RBACFieldPurgerTestRow(
                    id=field_uuid,
                    name=f"field-{i}",
                    owner_scope_type=ScopeType.USER.value,
                    owner_scope_id=user_id,
                    parent_entity_id=parent_entity_id,
                )
                db_sess.add(field_row)

                entity_field = EntityFieldRow(
                    entity_type=EntityType.SESSION.value,
                    entity_id=parent_entity_id,
                    field_type=FieldType.KERNEL.value,
                    field_id=str(field_uuid),
                )
                db_sess.add(entity_field)
            await db_sess.flush()

        yield BatchFieldsContext(
            field_uuids=field_uuids,
            parent_entity_id=parent_entity_id,
            user_id=user_id,
        )

    async def test_batch_purger_handles_field_scoped_entities(
        self,
        database_connection: ExtendedAsyncSAEngine,
        batch_fields: BatchFieldsContext,
    ) -> None:
        """Test that batch purger deletes field entities and EntityFieldRows."""

        async with database_connection.begin_session() as db_sess:
            # Verify initial state
            field_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACFieldPurgerTestRow)
            )
            assert field_count == 4

            entity_field_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(EntityFieldRow)
            )
            assert entity_field_count == 4

            # Execute batch purge
            spec = TestFieldBatchPurgerSpec()
            purger: RBACFieldBatchPurger[RBACFieldPurgerTestRow] = RBACFieldBatchPurger(spec=spec)
            result = await execute_rbac_field_batch_purger(db_sess, purger)

            # Verify result
            assert isinstance(result, RBACFieldBatchPurgerResult)
            assert result.deleted_count == 4
            assert result.deleted_entity_field_count == 4

            # Verify all fields deleted
            remaining_fields = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACFieldPurgerTestRow)
            )
            assert remaining_fields == 0

            # Verify all EntityFieldRows deleted
            remaining_entity_fields = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(EntityFieldRow)
            )
            assert remaining_entity_fields == 0

    async def test_batch_purger_handles_empty_batch(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test that batch purger handles empty results gracefully."""
        async with database_connection.begin_session() as db_sess:
            spec = TestFieldBatchPurgerSpec()
            purger: RBACFieldBatchPurger[RBACFieldPurgerTestRow] = RBACFieldBatchPurger(spec=spec)
            result = await execute_rbac_field_batch_purger(db_sess, purger)

            assert isinstance(result, RBACFieldBatchPurgerResult)
            assert result.deleted_count == 0
            assert result.deleted_entity_field_count == 0

    async def test_batch_purger_respects_batch_size(
        self,
        database_connection: ExtendedAsyncSAEngine,
        batch_fields: BatchFieldsContext,
    ) -> None:
        """Test that batch purger processes in batches according to batch_size."""

        async with database_connection.begin_session() as db_sess:
            # Execute batch purge with small batch size
            spec = TestFieldBatchPurgerSpec()
            purger: RBACFieldBatchPurger[RBACFieldPurgerTestRow] = RBACFieldBatchPurger(
                spec=spec,
                batch_size=2,  # Small batch size to force multiple iterations
            )
            result = await execute_rbac_field_batch_purger(db_sess, purger)

            # Should still delete all 4 fields across multiple batches
            assert result.deleted_count == 4
            assert result.deleted_entity_field_count == 4

            # Verify all fields deleted
            remaining_fields = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACFieldPurgerTestRow)
            )
            assert remaining_fields == 0


# =============================================================================
# Composite Primary Key Tests
# =============================================================================


class CompositePKFieldPurgerTestRow(Base):
    """ORM model with composite primary key for testing rejection."""

    __tablename__ = "test_rbac_field_purger_composite_pk"
    __table_args__ = {"extend_existing": True}

    tenant_id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)


class CompositePKFieldBatchPurgerSpec(RBACFieldBatchPurgerSpec[CompositePKFieldPurgerTestRow]):
    """Batch purger spec for composite PK testing."""

    def build_subquery(self) -> sa.Select[Any]:
        return sa.select(CompositePKFieldPurgerTestRow)

    def field_type(self) -> FieldType:
        return FieldType.KERNEL


class TestRBACFieldPurgerCompositePK:
    """Tests for composite primary key rejection in RBAC field purger."""

    async def test_single_purger_rejects_composite_pk(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> None:
        """Test that single field purger rejects composite PK tables."""
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: CompositePKFieldPurgerTestRow.__table__.create(c, checkfirst=True)
            )

        try:
            async with database_connection.begin_session() as db_sess:
                purger = RBACFieldPurger(
                    row_class=CompositePKFieldPurgerTestRow,
                    pk_value=1,  # PK value (error raised before lookup due to composite PK)
                    field_type=FieldType.KERNEL,
                    field_id="test-123",
                )

                with pytest.raises(UnsupportedCompositePrimaryKeyError):
                    await execute_rbac_field_purger(db_sess, purger)
        finally:
            async with database_connection.begin() as conn:
                await conn.run_sync(
                    lambda c: CompositePKFieldPurgerTestRow.__table__.drop(c, checkfirst=True)
                )

    async def test_batch_purger_rejects_composite_pk(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> None:
        """Test that batch field purger rejects composite PK tables."""
        async with database_connection.begin() as conn:
            await conn.run_sync(
                lambda c: CompositePKFieldPurgerTestRow.__table__.create(c, checkfirst=True)
            )

        try:
            async with database_connection.begin_session() as db_sess:
                spec = CompositePKFieldBatchPurgerSpec()
                purger = RBACFieldBatchPurger(spec=spec)

                with pytest.raises(UnsupportedCompositePrimaryKeyError):
                    await execute_rbac_field_batch_purger(db_sess, purger)
        finally:
            async with database_connection.begin() as conn:
                await conn.run_sync(
                    lambda c: CompositePKFieldPurgerTestRow.__table__.drop(c, checkfirst=True)
                )
