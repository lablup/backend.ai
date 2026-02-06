"""Integration tests for RBAC entity creator with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any
from uuid import UUID

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.data.permission.id import ScopeId as ScopeRef
from ai.backend.manager.data.permission.types import EntityType, ScopeType
from ai.backend.manager.errors.repository import UnsupportedCompositePrimaryKeyError
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.repositories.base.rbac.entity_creator import (
    RBACBulkEntityCreator,
    RBACBulkEntityCreatorResult,
    RBACEntityCreator,
    RBACEntityCreatorResult,
    execute_rbac_bulk_entity_creator,
    execute_rbac_entity_creator,
)
from ai.backend.manager.repositories.base.rbac.utils import insert_on_conflict_do_nothing
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


# =============================================================================
# Test Row Models
# =============================================================================


class RBACEntityCreatorTestRow(Base):  # type: ignore[misc]
    """ORM model for creator testing."""

    __tablename__ = "test_rbac_creator"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(
        GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    owner_scope_type: Mapped[str] = mapped_column(sa.String(32), nullable=False)
    owner_scope_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)


# =============================================================================
# Creator Spec Implementations
# =============================================================================


class SimpleCreatorSpec(CreatorSpec[RBACEntityCreatorTestRow]):
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
        self._entity_id = entity_id

    def build_row(self) -> RBACEntityCreatorTestRow:
        row_kwargs: dict[str, Any] = {
            "name": self._name,
            "owner_scope_type": self._scope_type.value,
            "owner_scope_id": self._scope_id,
        }
        if self._entity_id is not None:
            row_kwargs["id"] = self._entity_id
        return RBACEntityCreatorTestRow(**row_kwargs)


# =============================================================================
# Tables List
# =============================================================================

ENTITY_CREATOR_TABLES = [
    RBACEntityCreatorTestRow,
    AssociationScopesEntitiesRow,
]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def create_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    """Create RBAC entity creator test tables."""
    async with with_tables(database_connection, ENTITY_CREATOR_TABLES):  # type: ignore[arg-type]
        yield


# =============================================================================
# Single Entity Creator Tests
# =============================================================================


class TestRBACEntityCreatorBasic:
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
            spec = SimpleCreatorSpec(
                name="test-entity",
                scope_type=ScopeType.USER,
                scope_id=user_id,
            )
            creator: RBACEntityCreator[RBACEntityCreatorTestRow] = RBACEntityCreator(
                spec=spec,
                scope_ref=ScopeRef(ScopeType.USER, user_id),
                additional_scope_refs=[],
                entity_type=EntityType.VFOLDER,
            )
            result = await execute_rbac_entity_creator(db_sess, creator)

            # Verify result
            assert isinstance(result, RBACEntityCreatorResult)
            assert result.row.name == "test-entity"
            assert result.row.id is not None

            # Verify main row was inserted
            entity_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACEntityCreatorTestRow)
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
            spec = SimpleCreatorSpec(
                name="project-entity",
                scope_type=ScopeType.PROJECT,
                scope_id=project_id,
            )
            creator: RBACEntityCreator[RBACEntityCreatorTestRow] = RBACEntityCreator(
                spec=spec,
                scope_ref=ScopeRef(ScopeType.PROJECT, project_id),
                additional_scope_refs=[],
                entity_type=EntityType.VFOLDER,
            )
            await execute_rbac_entity_creator(db_sess, creator)

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
                spec = SimpleCreatorSpec(
                    name=f"entity-{i}",
                    scope_type=ScopeType.USER,
                    scope_id=user_id,
                )
                creator: RBACEntityCreator[RBACEntityCreatorTestRow] = RBACEntityCreator(
                    spec=spec,
                    scope_ref=ScopeRef(ScopeType.USER, user_id),
                    additional_scope_refs=[],
                    entity_type=EntityType.VFOLDER,
                )
                result = await execute_rbac_entity_creator(db_sess, creator)
                assert result.row.name == f"entity-{i}"

            # Verify counts
            entity_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACEntityCreatorTestRow)
            )
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert entity_count == 5
            assert assoc_count == 5

    async def test_create_entity_with_multiple_scopes(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test creating an entity with multiple scope associations."""
        user_id = str(uuid.uuid4())
        project_id = str(uuid.uuid4())

        async with database_connection.begin_session() as db_sess:
            spec = SimpleCreatorSpec(
                name="multi-scope-entity",
                scope_type=ScopeType.PROJECT,
                scope_id=project_id,
            )
            creator: RBACEntityCreator[RBACEntityCreatorTestRow] = RBACEntityCreator(
                spec=spec,
                scope_ref=ScopeRef(ScopeType.PROJECT, project_id),
                additional_scope_refs=[ScopeRef(ScopeType.USER, user_id)],
                entity_type=EntityType.VFOLDER,
            )
            result = await execute_rbac_entity_creator(db_sess, creator)

            # Verify result
            assert isinstance(result, RBACEntityCreatorResult)
            assert result.row.name == "multi-scope-entity"

            # Verify one main row was inserted
            entity_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACEntityCreatorTestRow)
            )
            assert entity_count == 1

            # Verify TWO associations were created (PROJECT + USER)
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 2

            # Verify association details
            assoc_rows = (await db_sess.scalars(sa.select(AssociationScopesEntitiesRow))).all()
            scope_types = {row.scope_type for row in assoc_rows}
            scope_ids = {row.scope_id for row in assoc_rows}

            assert ScopeType.PROJECT in scope_types
            assert ScopeType.USER in scope_types
            assert project_id in scope_ids
            assert user_id in scope_ids

            # All associations should point to the same entity
            entity_ids = {row.entity_id for row in assoc_rows}
            assert len(entity_ids) == 1
            assert str(result.row.id) in entity_ids


class TestRBACEntityCreatorIdempotent:
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
            spec1 = SimpleCreatorSpec(
                name="test-entity",
                scope_type=ScopeType.USER,
                scope_id=user_id,
                entity_id=entity_id,
            )
            creator1: RBACEntityCreator[RBACEntityCreatorTestRow] = RBACEntityCreator(
                spec=spec1,
                scope_ref=ScopeRef(ScopeType.USER, user_id),
                additional_scope_refs=[],
                entity_type=EntityType.VFOLDER,
            )
            result1 = await execute_rbac_entity_creator(db_sess, creator1)
            assert result1.row.id == entity_id

            # Verify one association created
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 1

        async with database_connection.begin_session() as db_sess:
            # Manually try to insert duplicate association (same scope, same entity_id)
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


# =============================================================================
# Bulk Entity Creator Tests
# =============================================================================


class TestRBACBulkEntityCreator:
    """Tests for bulk entity creator operations."""

    async def test_bulk_create_multiple_entities(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test bulk creating multiple entities."""
        user_id = str(uuid.uuid4())

        async with database_connection.begin_session() as db_sess:
            specs = [
                SimpleCreatorSpec(
                    name=f"entity-{i}",
                    scope_type=ScopeType.USER,
                    scope_id=user_id,
                )
                for i in range(5)
            ]
            creator: RBACBulkEntityCreator[RBACEntityCreatorTestRow] = RBACBulkEntityCreator(
                specs=specs,
                scope_type=ScopeType.USER,
                scope_id=user_id,
                entity_type=EntityType.VFOLDER,
            )
            result = await execute_rbac_bulk_entity_creator(db_sess, creator)

            # Verify result
            assert isinstance(result, RBACBulkEntityCreatorResult)
            assert len(result.rows) == 5
            for i, row in enumerate(result.rows):
                assert row.name == f"entity-{i}"

            # Verify counts
            entity_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACEntityCreatorTestRow)
            )
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert entity_count == 5
            assert assoc_count == 5

    async def test_bulk_create_with_empty_specs(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test bulk creating with empty specs returns empty result."""
        async with database_connection.begin_session() as db_sess:
            creator: RBACBulkEntityCreator[RBACEntityCreatorTestRow] = RBACBulkEntityCreator(
                specs=[],
                scope_type=ScopeType.USER,
                scope_id="dummy",
                entity_type=EntityType.VFOLDER,
            )
            result = await execute_rbac_bulk_entity_creator(db_sess, creator)

            assert isinstance(result, RBACBulkEntityCreatorResult)
            assert len(result.rows) == 0

            # Verify no entities created
            entity_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACEntityCreatorTestRow)
            )
            assert entity_count == 0

    async def test_bulk_create_entities_same_scope(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test bulk creating entities with same scope."""
        user_id = str(uuid.uuid4())

        async with database_connection.begin_session() as db_sess:
            specs = [
                SimpleCreatorSpec(
                    name="user-entity-1",
                    scope_type=ScopeType.USER,
                    scope_id=user_id,
                ),
                SimpleCreatorSpec(
                    name="user-entity-2",
                    scope_type=ScopeType.USER,
                    scope_id=user_id,
                ),
            ]
            creator: RBACBulkEntityCreator[RBACEntityCreatorTestRow] = RBACBulkEntityCreator(
                specs=specs,
                scope_type=ScopeType.USER,
                scope_id=user_id,
                entity_type=EntityType.VFOLDER,
            )
            result = await execute_rbac_bulk_entity_creator(db_sess, creator)

            assert len(result.rows) == 2

            # Verify associations
            assoc_rows = (await db_sess.scalars(sa.select(AssociationScopesEntitiesRow))).all()
            assert len(assoc_rows) == 2

            # All should have same scope
            for assoc in assoc_rows:
                assert assoc.scope_type == ScopeType.USER
                assert assoc.scope_id == user_id


# =============================================================================
# Composite Primary Key Tests
# =============================================================================


class CompositePKTestRow(Base):  # type: ignore[misc]
    """ORM model with composite primary key for testing rejection."""

    __tablename__ = "test_rbac_creator_composite_pk"
    __table_args__ = {"extend_existing": True}

    tenant_id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)


class CompositePKCreatorSpec(CreatorSpec[CompositePKTestRow]):
    """Creator spec for composite PK testing."""

    def __init__(self, tenant_id: int, item_id: int, name: str) -> None:
        self._tenant_id = tenant_id
        self._item_id = item_id
        self._name = name

    def build_row(self) -> CompositePKTestRow:
        return CompositePKTestRow(
            tenant_id=self._tenant_id,
            item_id=self._item_id,
            name=self._name,
        )


class TestRBACEntityCreatorCompositePK:
    """Tests for composite primary key rejection in RBAC entity creator."""

    async def test_single_creator_rejects_composite_pk(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> None:
        """Test that single entity creator rejects composite PK tables."""
        async with database_connection.begin() as conn:
            await conn.run_sync(lambda c: CompositePKTestRow.__table__.create(c, checkfirst=True))

        try:
            async with database_connection.begin_session() as db_sess:
                spec = CompositePKCreatorSpec(tenant_id=1, item_id=1, name="test")
                creator = RBACEntityCreator(
                    spec=spec,
                    scope_ref=ScopeRef(ScopeType.USER, "user-123"),
                    additional_scope_refs=[],
                    entity_type=EntityType.VFOLDER,
                )

                with pytest.raises(UnsupportedCompositePrimaryKeyError):
                    await execute_rbac_entity_creator(db_sess, creator)
        finally:
            async with database_connection.begin() as conn:
                await conn.run_sync(lambda c: CompositePKTestRow.__table__.drop(c, checkfirst=True))

    async def test_bulk_creator_rejects_composite_pk(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> None:
        """Test that bulk entity creator rejects composite PK tables."""
        async with database_connection.begin() as conn:
            await conn.run_sync(lambda c: CompositePKTestRow.__table__.create(c, checkfirst=True))

        try:
            async with database_connection.begin_session() as db_sess:
                specs = [
                    CompositePKCreatorSpec(tenant_id=1, item_id=i, name=f"test-{i}")
                    for i in range(3)
                ]
                creator = RBACBulkEntityCreator(
                    specs=specs,
                    scope_type=ScopeType.USER,
                    scope_id="user-123",
                    entity_type=EntityType.VFOLDER,
                )

                with pytest.raises(UnsupportedCompositePrimaryKeyError):
                    await execute_rbac_bulk_entity_creator(db_sess, creator)
        finally:
            async with database_connection.begin() as conn:
                await conn.run_sync(lambda c: CompositePKTestRow.__table__.drop(c, checkfirst=True))
