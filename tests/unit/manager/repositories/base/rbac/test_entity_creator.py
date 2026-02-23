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
from ai.backend.manager.data.permission.types import EntityType, RBACElementType, ScopeType
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
    execute_rbac_entity_creators,
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


class CompositePKTestRow(Base):  # type: ignore[misc]
    """ORM model with composite primary key for testing rejection."""

    __tablename__ = "test_rbac_creator_composite_pk"
    __table_args__ = {"extend_existing": True}

    tenant_id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(50), nullable=False)


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


# =============================================================================
# Tables List
# =============================================================================

ENTITY_CREATOR_TABLES = [
    RBACEntityCreatorTestRow,
    AssociationScopesEntitiesRow,
]


# =============================================================================
# Common Fixtures
# =============================================================================


@pytest.fixture
async def create_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    """Create RBAC entity creator test tables."""
    async with with_tables(database_connection, ENTITY_CREATOR_TABLES):  # type: ignore[arg-type]
        yield


@pytest.fixture
async def create_composite_pk_table(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    """Create and drop composite PK test table."""
    async with database_connection.begin() as conn:
        await conn.run_sync(lambda c: CompositePKTestRow.__table__.create(c, checkfirst=True))
    yield
    async with database_connection.begin() as conn:
        await conn.run_sync(lambda c: CompositePKTestRow.__table__.drop(c, checkfirst=True))


@pytest.fixture
def user_scope_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def user_scope_id_2() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def project_scope_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def fixed_entity_id() -> UUID:
    return uuid.uuid4()


# =============================================================================
# Single Entity Creator Fixtures
# =============================================================================


@pytest.fixture
def single_creator_user_scope(
    user_scope_id: str,
) -> RBACEntityCreator[RBACEntityCreatorTestRow]:
    return RBACEntityCreator(
        spec=SimpleCreatorSpec(
            name="test-entity",
            scope_type=ScopeType.USER,
            scope_id=user_scope_id,
        ),
        element_type=RBACElementType.VFOLDER,
        scope_ref=ScopeRef(ScopeType.USER, user_scope_id),
        additional_scope_refs=[],
    )


@pytest.fixture
def single_creator_project_scope(
    project_scope_id: str,
) -> RBACEntityCreator[RBACEntityCreatorTestRow]:
    return RBACEntityCreator(
        spec=SimpleCreatorSpec(
            name="project-entity",
            scope_type=ScopeType.PROJECT,
            scope_id=project_scope_id,
        ),
        element_type=RBACElementType.VFOLDER,
        scope_ref=ScopeRef(ScopeType.PROJECT, project_scope_id),
        additional_scope_refs=[],
    )


@pytest.fixture
def sequential_creators(
    user_scope_id: str,
) -> list[RBACEntityCreator[RBACEntityCreatorTestRow]]:
    return [
        RBACEntityCreator(
            spec=SimpleCreatorSpec(
                name=f"entity-{i}",
                scope_type=ScopeType.USER,
                scope_id=user_scope_id,
            ),
            element_type=RBACElementType.VFOLDER,
            scope_ref=ScopeRef(ScopeType.USER, user_scope_id),
            additional_scope_refs=[],
        )
        for i in range(5)
    ]


@pytest.fixture
def multi_scope_creator(
    user_scope_id: str,
    project_scope_id: str,
) -> RBACEntityCreator[RBACEntityCreatorTestRow]:
    return RBACEntityCreator(
        spec=SimpleCreatorSpec(
            name="multi-scope-entity",
            scope_type=ScopeType.PROJECT,
            scope_id=project_scope_id,
        ),
        element_type=RBACElementType.VFOLDER,
        scope_ref=ScopeRef(ScopeType.PROJECT, project_scope_id),
        additional_scope_refs=[ScopeRef(ScopeType.USER, user_scope_id)],
    )


# =============================================================================
# Idempotent Test Fixtures
# =============================================================================


@pytest.fixture
def idempotent_creator(
    user_scope_id: str,
    fixed_entity_id: UUID,
) -> RBACEntityCreator[RBACEntityCreatorTestRow]:
    return RBACEntityCreator(
        spec=SimpleCreatorSpec(
            name="test-entity",
            scope_type=ScopeType.USER,
            scope_id=user_scope_id,
            entity_id=fixed_entity_id,
        ),
        element_type=RBACElementType.VFOLDER,
        scope_ref=ScopeRef(ScopeType.USER, user_scope_id),
        additional_scope_refs=[],
    )


@pytest.fixture
async def existing_entity(
    database_connection: ExtendedAsyncSAEngine,
    create_tables: None,
    idempotent_creator: RBACEntityCreator[RBACEntityCreatorTestRow],
) -> RBACEntityCreatorResult[RBACEntityCreatorTestRow]:
    """Create an entity in the DB as prerequisite for idempotent tests."""
    async with database_connection.begin_session() as db_sess:
        return await execute_rbac_entity_creator(db_sess, idempotent_creator)


# =============================================================================
# Bulk Entity Creator Fixtures
# =============================================================================


@pytest.fixture
def bulk_creator_five_entities(
    user_scope_id: str,
) -> RBACBulkEntityCreator[RBACEntityCreatorTestRow]:
    return RBACBulkEntityCreator(
        specs=[
            SimpleCreatorSpec(
                name=f"entity-{i}",
                scope_type=ScopeType.USER,
                scope_id=user_scope_id,
            )
            for i in range(5)
        ],
        element_type=RBACElementType.VFOLDER,
        scope_ref=ScopeRef(ScopeType.USER, user_scope_id),
    )


@pytest.fixture
def bulk_creator_empty() -> RBACBulkEntityCreator[RBACEntityCreatorTestRow]:
    return RBACBulkEntityCreator(
        specs=[],
        element_type=RBACElementType.VFOLDER,
        scope_ref=ScopeRef(ScopeType.USER, "dummy"),
    )


@pytest.fixture
def bulk_creator_two_same_scope(
    user_scope_id: str,
) -> RBACBulkEntityCreator[RBACEntityCreatorTestRow]:
    return RBACBulkEntityCreator(
        specs=[
            SimpleCreatorSpec(
                name="user-entity-1",
                scope_type=ScopeType.USER,
                scope_id=user_scope_id,
            ),
            SimpleCreatorSpec(
                name="user-entity-2",
                scope_type=ScopeType.USER,
                scope_id=user_scope_id,
            ),
        ],
        element_type=RBACElementType.VFOLDER,
        scope_ref=ScopeRef(ScopeType.USER, user_scope_id),
    )


# =============================================================================
# Batch Entity Creators Fixtures (for execute_rbac_entity_creators)
# =============================================================================


@pytest.fixture
def batch_creators_same_scope(
    user_scope_id: str,
) -> list[RBACEntityCreator[RBACEntityCreatorTestRow]]:
    return [
        RBACEntityCreator(
            spec=SimpleCreatorSpec(
                name=f"entity-{i}",
                scope_type=ScopeType.USER,
                scope_id=user_scope_id,
            ),
            element_type=RBACElementType.VFOLDER,
            scope_ref=ScopeRef(ScopeType.USER, user_scope_id),
            additional_scope_refs=[],
        )
        for i in range(5)
    ]


@pytest.fixture
def batch_creators_different_scopes(
    user_scope_id: str,
    project_scope_id: str,
) -> list[RBACEntityCreator[RBACEntityCreatorTestRow]]:
    return [
        RBACEntityCreator(
            spec=SimpleCreatorSpec(
                name="user-entity",
                scope_type=ScopeType.USER,
                scope_id=user_scope_id,
            ),
            element_type=RBACElementType.VFOLDER,
            scope_ref=ScopeRef(ScopeType.USER, user_scope_id),
            additional_scope_refs=[],
        ),
        RBACEntityCreator(
            spec=SimpleCreatorSpec(
                name="project-entity",
                scope_type=ScopeType.PROJECT,
                scope_id=project_scope_id,
            ),
            element_type=RBACElementType.VFOLDER,
            scope_ref=ScopeRef(ScopeType.PROJECT, project_scope_id),
            additional_scope_refs=[],
        ),
    ]


@pytest.fixture
def batch_creators_additional_scopes(
    user_scope_id: str,
    user_scope_id_2: str,
    project_scope_id: str,
) -> list[RBACEntityCreator[RBACEntityCreatorTestRow]]:
    return [
        RBACEntityCreator(
            spec=SimpleCreatorSpec(
                name="multi-scope-1",
                scope_type=ScopeType.PROJECT,
                scope_id=project_scope_id,
            ),
            element_type=RBACElementType.VFOLDER,
            scope_ref=ScopeRef(ScopeType.PROJECT, project_scope_id),
            additional_scope_refs=[ScopeRef(ScopeType.USER, user_scope_id)],
        ),
        RBACEntityCreator(
            spec=SimpleCreatorSpec(
                name="multi-scope-2",
                scope_type=ScopeType.USER,
                scope_id=user_scope_id_2,
            ),
            element_type=RBACElementType.VFOLDER,
            scope_ref=ScopeRef(ScopeType.USER, user_scope_id_2),
            additional_scope_refs=[ScopeRef(ScopeType.PROJECT, project_scope_id)],
        ),
    ]


# =============================================================================
# Composite PK Creator Fixtures
# =============================================================================


@pytest.fixture
def composite_pk_single_creator() -> RBACEntityCreator[CompositePKTestRow]:
    return RBACEntityCreator(
        spec=CompositePKCreatorSpec(tenant_id=1, item_id=1, name="test"),
        element_type=RBACElementType.VFOLDER,
        scope_ref=ScopeRef(ScopeType.USER, "user-123"),
        additional_scope_refs=[],
    )


@pytest.fixture
def composite_pk_bulk_creator() -> RBACBulkEntityCreator[CompositePKTestRow]:
    return RBACBulkEntityCreator(
        specs=[CompositePKCreatorSpec(tenant_id=1, item_id=i, name=f"test-{i}") for i in range(3)],
        element_type=RBACElementType.VFOLDER,
        scope_ref=ScopeRef(ScopeType.USER, "user-123"),
    )


@pytest.fixture
def composite_pk_batch_creators() -> list[RBACEntityCreator[CompositePKTestRow]]:
    return [
        RBACEntityCreator(
            spec=CompositePKCreatorSpec(tenant_id=1, item_id=i, name=f"test-{i}"),
            element_type=RBACElementType.VFOLDER,
            scope_ref=ScopeRef(ScopeType.USER, "user-123"),
            additional_scope_refs=[],
        )
        for i in range(3)
    ]


# =============================================================================
# Single Entity Creator Tests
# =============================================================================


class TestRBACEntityCreatorBasic:
    """Basic tests for RBAC entity creator operations."""

    async def test_create_entity_inserts_row_and_association(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        single_creator_user_scope: RBACEntityCreator[RBACEntityCreatorTestRow],
        user_scope_id: str,
    ) -> None:
        """Test creating an entity inserts both main row and scope association."""
        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_entity_creator(db_sess, single_creator_user_scope)

            assert isinstance(result, RBACEntityCreatorResult)
            assert result.row.name == "test-entity"
            assert result.row.id is not None

            entity_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACEntityCreatorTestRow)
            )
            assert entity_count == 1

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 1

            assoc_row = await db_sess.scalar(sa.select(AssociationScopesEntitiesRow))
            assert assoc_row is not None
            assert assoc_row.scope_type == ScopeType.USER
            assert assoc_row.scope_id == user_scope_id
            assert assoc_row.entity_type == EntityType.VFOLDER
            assert assoc_row.entity_id == str(result.row.id)

    async def test_create_entity_with_project_scope(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        single_creator_project_scope: RBACEntityCreator[RBACEntityCreatorTestRow],
        project_scope_id: str,
    ) -> None:
        """Test creating an entity with project scope."""
        async with database_connection.begin_session() as db_sess:
            await execute_rbac_entity_creator(db_sess, single_creator_project_scope)

            assoc_row = await db_sess.scalar(sa.select(AssociationScopesEntitiesRow))
            assert assoc_row is not None
            assert assoc_row.scope_type == ScopeType.PROJECT
            assert assoc_row.scope_id == project_scope_id

    async def test_create_multiple_entities_sequentially(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        sequential_creators: list[RBACEntityCreator[RBACEntityCreatorTestRow]],
    ) -> None:
        """Test creating multiple entities in sequence."""
        async with database_connection.begin_session() as db_sess:
            for i, creator in enumerate(sequential_creators):
                result = await execute_rbac_entity_creator(db_sess, creator)
                assert result.row.name == f"entity-{i}"

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
        multi_scope_creator: RBACEntityCreator[RBACEntityCreatorTestRow],
        user_scope_id: str,
        project_scope_id: str,
    ) -> None:
        """Test creating an entity with multiple scope associations."""
        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_entity_creator(db_sess, multi_scope_creator)

            assert isinstance(result, RBACEntityCreatorResult)
            assert result.row.name == "multi-scope-entity"

            entity_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACEntityCreatorTestRow)
            )
            assert entity_count == 1

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 2

            assoc_rows = (await db_sess.scalars(sa.select(AssociationScopesEntitiesRow))).all()
            scope_types = {row.scope_type for row in assoc_rows}
            scope_ids = {row.scope_id for row in assoc_rows}

            assert ScopeType.PROJECT in scope_types
            assert ScopeType.USER in scope_types
            assert project_scope_id in scope_ids
            assert user_scope_id in scope_ids

            entity_ids = {row.entity_id for row in assoc_rows}
            assert len(entity_ids) == 1
            assert str(result.row.id) in entity_ids


class TestRBACEntityCreatorIdempotent:
    """Tests for idempotent behavior of RBAC entity creator."""

    async def test_creator_handles_duplicate_association_gracefully(
        self,
        database_connection: ExtendedAsyncSAEngine,
        existing_entity: RBACEntityCreatorResult[RBACEntityCreatorTestRow],
        user_scope_id: str,
        fixed_entity_id: UUID,
    ) -> None:
        """Test that creating entity with existing association doesn't fail.

        The creator uses insert_on_conflict_do_nothing, so duplicate associations
        should be handled gracefully without errors.
        """
        assert existing_entity.row.id == fixed_entity_id

        async with database_connection.begin_session() as db_sess:
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 1

            duplicate_assoc = AssociationScopesEntitiesRow(
                scope_type=ScopeType.USER,
                scope_id=user_scope_id,
                entity_type=EntityType.VFOLDER,
                entity_id=str(fixed_entity_id),
            )
            await insert_on_conflict_do_nothing(db_sess, duplicate_assoc)

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
        bulk_creator_five_entities: RBACBulkEntityCreator[RBACEntityCreatorTestRow],
    ) -> None:
        """Test bulk creating multiple entities."""
        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_bulk_entity_creator(db_sess, bulk_creator_five_entities)

            assert isinstance(result, RBACBulkEntityCreatorResult)
            assert len(result.rows) == 5
            for i, row in enumerate(result.rows):
                assert row.name == f"entity-{i}"

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
        bulk_creator_empty: RBACBulkEntityCreator[RBACEntityCreatorTestRow],
    ) -> None:
        """Test bulk creating with empty specs returns empty result."""
        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_bulk_entity_creator(db_sess, bulk_creator_empty)

            assert isinstance(result, RBACBulkEntityCreatorResult)
            assert len(result.rows) == 0

            entity_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACEntityCreatorTestRow)
            )
            assert entity_count == 0

    async def test_bulk_create_entities_same_scope(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        bulk_creator_two_same_scope: RBACBulkEntityCreator[RBACEntityCreatorTestRow],
        user_scope_id: str,
    ) -> None:
        """Test bulk creating entities with same scope."""
        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_bulk_entity_creator(db_sess, bulk_creator_two_same_scope)

            assert len(result.rows) == 2

            assoc_rows = (await db_sess.scalars(sa.select(AssociationScopesEntitiesRow))).all()
            assert len(assoc_rows) == 2

            for assoc in assoc_rows:
                assert assoc.scope_type == ScopeType.USER
                assert assoc.scope_id == user_scope_id


# =============================================================================
# Composite Primary Key Tests
# =============================================================================


class TestRBACEntityCreatorCompositePK:
    """Tests for composite primary key rejection in RBAC entity creator."""

    async def test_single_creator_rejects_composite_pk(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_composite_pk_table: None,
        composite_pk_single_creator: RBACEntityCreator[CompositePKTestRow],
    ) -> None:
        """Test that single entity creator rejects composite PK tables."""
        async with database_connection.begin_session() as db_sess:
            with pytest.raises(UnsupportedCompositePrimaryKeyError):
                await execute_rbac_entity_creator(db_sess, composite_pk_single_creator)

    async def test_bulk_creator_rejects_composite_pk(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_composite_pk_table: None,
        composite_pk_bulk_creator: RBACBulkEntityCreator[CompositePKTestRow],
    ) -> None:
        """Test that bulk entity creator rejects composite PK tables."""
        async with database_connection.begin_session() as db_sess:
            with pytest.raises(UnsupportedCompositePrimaryKeyError):
                await execute_rbac_bulk_entity_creator(db_sess, composite_pk_bulk_creator)

    async def test_batch_creators_rejects_composite_pk(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_composite_pk_table: None,
        composite_pk_batch_creators: list[RBACEntityCreator[CompositePKTestRow]],
    ) -> None:
        """Test that batch entity creators rejects composite PK tables."""
        async with database_connection.begin_session() as db_sess:
            with pytest.raises(UnsupportedCompositePrimaryKeyError):
                await execute_rbac_entity_creators(db_sess, composite_pk_batch_creators)


# =============================================================================
# Batch Entity Creators Tests (execute_rbac_entity_creators)
# =============================================================================


class TestExecuteRBACEntityCreators:
    """Tests for batch execution of multiple RBACEntityCreator instances."""

    async def test_batch_create_with_empty_list(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Test batch creating with empty list returns empty result."""
        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_entity_creators(db_sess, [])

            assert isinstance(result, RBACBulkEntityCreatorResult)
            assert len(result.rows) == 0

    async def test_batch_create_entities_with_same_scope(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        batch_creators_same_scope: list[RBACEntityCreator[RBACEntityCreatorTestRow]],
    ) -> None:
        """Test batch creating entities all sharing the same scope."""
        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_entity_creators(db_sess, batch_creators_same_scope)

            assert isinstance(result, RBACBulkEntityCreatorResult)
            assert len(result.rows) == 5
            for i, row in enumerate(result.rows):
                assert row.name == f"entity-{i}"
                assert row.id is not None

            entity_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(RBACEntityCreatorTestRow)
            )
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert entity_count == 5
            assert assoc_count == 5

    async def test_batch_create_entities_with_different_scopes(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        batch_creators_different_scopes: list[RBACEntityCreator[RBACEntityCreatorTestRow]],
        user_scope_id: str,
        project_scope_id: str,
    ) -> None:
        """Test batch creating entities where each has a different scope."""
        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_entity_creators(db_sess, batch_creators_different_scopes)

            assert len(result.rows) == 2
            assert result.rows[0].name == "user-entity"
            assert result.rows[1].name == "project-entity"

            assoc_rows = (await db_sess.scalars(sa.select(AssociationScopesEntitiesRow))).all()
            assert len(assoc_rows) == 2

            scope_map = {row.entity_id: (row.scope_type, row.scope_id) for row in assoc_rows}
            assert scope_map[str(result.rows[0].id)] == (ScopeType.USER, user_scope_id)
            assert scope_map[str(result.rows[1].id)] == (ScopeType.PROJECT, project_scope_id)

    async def test_batch_create_entities_with_additional_scopes(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        batch_creators_additional_scopes: list[RBACEntityCreator[RBACEntityCreatorTestRow]],
    ) -> None:
        """Test batch creating entities where each has additional scope refs."""
        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_entity_creators(db_sess, batch_creators_additional_scopes)

            assert len(result.rows) == 2

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 4

            entity_1_id = str(result.rows[0].id)
            entity_2_id = str(result.rows[1].id)

            entity_1_assocs = (
                await db_sess.scalars(
                    sa.select(AssociationScopesEntitiesRow).where(
                        AssociationScopesEntitiesRow.entity_id == entity_1_id,
                    )
                )
            ).all()
            assert len(entity_1_assocs) == 2
            entity_1_scope_types = {a.scope_type for a in entity_1_assocs}
            assert ScopeType.PROJECT in entity_1_scope_types
            assert ScopeType.USER in entity_1_scope_types

            entity_2_assocs = (
                await db_sess.scalars(
                    sa.select(AssociationScopesEntitiesRow).where(
                        AssociationScopesEntitiesRow.entity_id == entity_2_id,
                    )
                )
            ).all()
            assert len(entity_2_assocs) == 2
            entity_2_scope_types = {a.scope_type for a in entity_2_assocs}
            assert ScopeType.USER in entity_2_scope_types
            assert ScopeType.PROJECT in entity_2_scope_types
