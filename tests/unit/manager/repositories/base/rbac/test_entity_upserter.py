"""Integration tests for RBAC entity upserter with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.data.permission.types import (
    EntityType,
    RBACElementRef,
    RBACElementType,
    ScopeType,
)
from ai.backend.manager.errors.repository import UnsupportedCompositePrimaryKeyError
from ai.backend.manager.models.base import Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.repositories.base.rbac.entity_upserter import (
    RBACEntityUpserter,
    RBACEntityUpserterResult,
    execute_rbac_entity_upserter,
)
from ai.backend.manager.repositories.base.upserter import Upserter, UpserterSpec
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


# =============================================================================
# Test Row Models
# =============================================================================


class RBACEntityUpserterTestRow(Base):  # type: ignore[misc]
    """ORM model for upserter testing with string PK."""

    __tablename__ = "test_rbac_upserter"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(sa.String(64), primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    version: Mapped[int] = mapped_column(sa.Integer, nullable=False, server_default=sa.text("1"))


class CompositePKUpserterTestRow(Base):  # type: ignore[misc]
    """ORM model with composite primary key for testing rejection."""

    __tablename__ = "test_rbac_upserter_composite_pk"
    __table_args__ = {"extend_existing": True}

    tenant_id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)


# =============================================================================
# UpserterSpec Implementations
# =============================================================================


class SimpleUpserterSpec(UpserterSpec[RBACEntityUpserterTestRow]):
    """Simple upserter spec for testing."""

    def __init__(self, entity_id: str, name: str, version: int = 1) -> None:
        self._entity_id = entity_id
        self._name = name
        self._version = version

    @property
    def row_class(self) -> type[RBACEntityUpserterTestRow]:
        return RBACEntityUpserterTestRow

    def build_insert_values(self) -> dict[str, Any]:
        return {
            "id": self._entity_id,
            "name": self._name,
            "version": self._version,
        }

    def build_update_values(self) -> dict[str, Any]:
        return {
            "name": self._name,
            "version": self._version,
        }


class CompositePKUpserterSpec(UpserterSpec[CompositePKUpserterTestRow]):
    """Upserter spec for composite PK testing."""

    def __init__(self, tenant_id: int, item_id: int, name: str) -> None:
        self._tenant_id = tenant_id
        self._item_id = item_id
        self._name = name

    @property
    def row_class(self) -> type[CompositePKUpserterTestRow]:
        return CompositePKUpserterTestRow

    def build_insert_values(self) -> dict[str, Any]:
        return {
            "tenant_id": self._tenant_id,
            "item_id": self._item_id,
            "name": self._name,
        }

    def build_update_values(self) -> dict[str, Any]:
        return {"name": self._name}


# =============================================================================
# Tables List
# =============================================================================

ENTITY_UPSERTER_TABLES = [
    RBACEntityUpserterTestRow,
    AssociationScopesEntitiesRow,
]


# =============================================================================
# Common Fixtures
# =============================================================================


@pytest.fixture
async def create_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    """Create RBAC entity upserter test tables."""
    async with with_tables(database_connection, ENTITY_UPSERTER_TABLES):  # type: ignore[arg-type]
        yield


@pytest.fixture
async def create_composite_pk_table(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    """Create and drop composite PK test table."""
    async with database_connection.begin() as conn:
        await conn.run_sync(
            lambda c: CompositePKUpserterTestRow.__table__.create(c, checkfirst=True)
        )
    yield
    async with database_connection.begin() as conn:
        await conn.run_sync(lambda c: CompositePKUpserterTestRow.__table__.drop(c, checkfirst=True))


@pytest.fixture
def entity_id() -> str:
    return f"entity-{uuid.uuid4()}"


@pytest.fixture
def scope_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def scope_id_2() -> str:
    return str(uuid.uuid4())


# =============================================================================
# Insert Tests
# =============================================================================


class TestRBACEntityUpserterInsert:
    """Tests for RBAC entity upserter INSERT path."""

    async def test_insert_creates_row_and_association(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        scope_id: str,
    ) -> None:
        """First upsert inserts row and creates RBAC association."""
        rbac_upserter = RBACEntityUpserter(
            upserter=Upserter(spec=SimpleUpserterSpec(entity_id=entity_id, name="test-entity")),
            element_type=RBACElementType.VFOLDER,
            scope_ref=RBACElementRef(RBACElementType.USER, scope_id),
            index_elements=["id"],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_entity_upserter(db_sess, rbac_upserter)

            assert isinstance(result, RBACEntityUpserterResult)
            assert result.row.id == entity_id
            assert result.row.name == "test-entity"
            assert result.was_inserted is True

            entity_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACEntityUpserterTestRow)
            )
            assert entity_count == 1

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 1

            assoc_row = await db_sess.scalar(sa.select(AssociationScopesEntitiesRow))
            assert assoc_row is not None
            assert assoc_row.scope_type == ScopeType.USER
            assert assoc_row.scope_id == scope_id
            assert assoc_row.entity_type == EntityType.VFOLDER
            assert assoc_row.entity_id == entity_id

    async def test_insert_with_multiple_scopes(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        scope_id: str,
        scope_id_2: str,
    ) -> None:
        """First upsert with additional_scope_refs creates multiple associations."""
        rbac_upserter = RBACEntityUpserter(
            upserter=Upserter(
                spec=SimpleUpserterSpec(entity_id=entity_id, name="multi-scope-entity"),
            ),
            element_type=RBACElementType.VFOLDER,
            scope_ref=RBACElementRef(RBACElementType.PROJECT, scope_id),
            additional_scope_refs=[RBACElementRef(RBACElementType.USER, scope_id_2)],
            index_elements=["id"],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_entity_upserter(db_sess, rbac_upserter)

            assert result.was_inserted is True

            entity_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACEntityUpserterTestRow)
            )
            assert entity_count == 1

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 2

            assoc_rows = (await db_sess.scalars(sa.select(AssociationScopesEntitiesRow))).all()
            scope_types = {row.scope_type for row in assoc_rows}
            assert ScopeType.PROJECT in scope_types
            assert ScopeType.USER in scope_types


# =============================================================================
# Update Tests
# =============================================================================


class TestRBACEntityUpserterUpdate:
    """Tests for RBAC entity upserter UPDATE path."""

    async def test_update_skips_association(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        scope_id: str,
    ) -> None:
        """Second upsert with same PK updates row but creates no new association."""
        rbac_upserter_v1 = RBACEntityUpserter(
            upserter=Upserter(
                spec=SimpleUpserterSpec(entity_id=entity_id, name="entity-v1", version=1),
            ),
            element_type=RBACElementType.VFOLDER,
            scope_ref=RBACElementRef(RBACElementType.USER, scope_id),
            index_elements=["id"],
        )
        rbac_upserter_v2 = RBACEntityUpserter(
            upserter=Upserter(
                spec=SimpleUpserterSpec(entity_id=entity_id, name="entity-v2", version=2),
            ),
            element_type=RBACElementType.VFOLDER,
            scope_ref=RBACElementRef(RBACElementType.USER, scope_id),
            index_elements=["id"],
        )

        async with database_connection.begin_session() as db_sess:
            result1 = await execute_rbac_entity_upserter(db_sess, rbac_upserter_v1)
            assert result1.was_inserted is True

        async with database_connection.begin_session() as db_sess:
            result2 = await execute_rbac_entity_upserter(db_sess, rbac_upserter_v2)
            assert result2.was_inserted is False

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 1

    async def test_update_changes_values(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        scope_id: str,
    ) -> None:
        """Update path applies update_values from the spec."""
        rbac_upserter_v1 = RBACEntityUpserter(
            upserter=Upserter(
                spec=SimpleUpserterSpec(entity_id=entity_id, name="original", version=1),
            ),
            element_type=RBACElementType.VFOLDER,
            scope_ref=RBACElementRef(RBACElementType.USER, scope_id),
            index_elements=["id"],
        )
        rbac_upserter_v2 = RBACEntityUpserter(
            upserter=Upserter(
                spec=SimpleUpserterSpec(entity_id=entity_id, name="updated", version=2),
            ),
            element_type=RBACElementType.VFOLDER,
            scope_ref=RBACElementRef(RBACElementType.USER, scope_id),
            index_elements=["id"],
        )

        async with database_connection.begin_session() as db_sess:
            await execute_rbac_entity_upserter(db_sess, rbac_upserter_v1)

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_entity_upserter(db_sess, rbac_upserter_v2)

            assert result.row.name == "updated"
            assert result.row.version == 2
            assert result.was_inserted is False

    async def test_repeated_upserts_single_association(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        scope_id: str,
    ) -> None:
        """Multiple upserts of same PK produce only one association (idempotency)."""
        for i in range(5):
            rbac_upserter = RBACEntityUpserter(
                upserter=Upserter(
                    spec=SimpleUpserterSpec(entity_id=entity_id, name=f"entity-v{i}", version=i),
                ),
                element_type=RBACElementType.VFOLDER,
                scope_ref=RBACElementRef(RBACElementType.USER, scope_id),
                index_elements=["id"],
            )
            async with database_connection.begin_session() as db_sess:
                result = await execute_rbac_entity_upserter(db_sess, rbac_upserter)
                if i == 0:
                    assert result.was_inserted is True
                else:
                    assert result.was_inserted is False

        async with database_connection.begin_session() as db_sess:
            entity_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACEntityUpserterTestRow)
            )
            assert entity_count == 1

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 1


# =============================================================================
# Composite Primary Key Tests
# =============================================================================


class TestRBACEntityUpserterCompositePK:
    """Tests for composite primary key rejection in RBAC entity upserter."""

    async def test_rejects_composite_pk_on_insert(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_composite_pk_table: None,
    ) -> None:
        """Upserter rejects composite PK tables on INSERT path."""
        rbac_upserter = RBACEntityUpserter(
            upserter=Upserter(
                spec=CompositePKUpserterSpec(tenant_id=1, item_id=1, name="test"),
            ),
            element_type=RBACElementType.VFOLDER,
            scope_ref=RBACElementRef(RBACElementType.USER, "user-123"),
            index_elements=["tenant_id", "item_id"],
        )

        async with database_connection.begin_session(commit_on_end=False) as db_sess:
            with pytest.raises(UnsupportedCompositePrimaryKeyError):
                await execute_rbac_entity_upserter(db_sess, rbac_upserter)
