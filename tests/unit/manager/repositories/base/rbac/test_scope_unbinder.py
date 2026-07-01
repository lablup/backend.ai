"""Integration tests for RBAC scope unbinder with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.data.permission.types import (
    EntityType,
    RBACElementRef,
    RBACElementType,
    ScopeType,
)
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.repositories.base.purger import BatchPurgerSpec
from ai.backend.manager.repositories.base.rbac.scope_unbinder import (
    RBACScopeEntityUnbinder,
    RBACUnbinderResult,
    execute_rbac_scope_entity_unbinder,
)
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


# =============================================================================
# Test Row Model (N:N mapping table)
# =============================================================================


class ScopeUnbinderMappingRow(Base):  # type: ignore[misc]
    """N:N mapping row for scope unbinder testing."""

    __tablename__ = "test_scope_unbinder_mapping"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    entity_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    scope_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)


# =============================================================================
# Unbinder Implementation
# =============================================================================


class TestScopeEntityUnbinder(RBACScopeEntityUnbinder[ScopeUnbinderMappingRow]):
    """Scope-wide entity unbinder for testing: delete entities from a scope."""

    def __init__(
        self,
        entity_ids: Sequence[str] | None,
        entity_element_type: RBACElementType,
        scope_id: str,
        scope_element_type: RBACElementType,
    ) -> None:
        self._entity_ids_value = entity_ids
        self._entity_element_type = entity_element_type
        self._scope_id = scope_id
        self._scope_element_type = scope_element_type

    def build_purger_spec(self) -> BatchPurgerSpec[ScopeUnbinderMappingRow]:
        entity_ids = self._entity_ids_value
        scope_id = self._scope_id

        class _Spec(BatchPurgerSpec[ScopeUnbinderMappingRow]):
            def build_subquery(self) -> sa.sql.Select[tuple[ScopeUnbinderMappingRow]]:
                stmt = sa.select(ScopeUnbinderMappingRow).where(
                    ScopeUnbinderMappingRow.scope_id == scope_id,
                )
                if entity_ids is not None:
                    stmt = stmt.where(
                        ScopeUnbinderMappingRow.entity_id.in_(entity_ids),
                    )
                return stmt

        return _Spec()

    @property
    def entity_type(self) -> RBACElementType:
        return self._entity_element_type

    @property
    def scope_ref(self) -> RBACElementRef:
        return RBACElementRef(self._scope_element_type, self._scope_id)

    @property
    def entity_ids(self) -> Sequence[str] | None:
        return self._entity_ids_value


# =============================================================================
# Tables & Fixtures
# =============================================================================

UNBINDER_TABLES = [
    ScopeUnbinderMappingRow,
    AssociationScopesEntitiesRow,
]


@dataclass
class UnbinderSeedContext:
    """Seed data: 2 entities x 2 scopes = 4 mapping rows + 4 association rows."""

    entity_id_1: str
    entity_id_2: str
    scope_id_a: str
    scope_id_b: str


@pytest.fixture
async def create_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    async with with_tables(database_connection, UNBINDER_TABLES):  # type: ignore[arg-type]
        yield


@pytest.fixture
async def seed_data(
    database_connection: ExtendedAsyncSAEngine,
    create_tables: None,
) -> AsyncGenerator[UnbinderSeedContext, None]:
    """Seed 2 entities x 2 scopes (4 mapping rows + 4 association rows)."""
    entity_id_1 = str(uuid.uuid4())
    entity_id_2 = str(uuid.uuid4())
    scope_id_a = str(uuid.uuid4())
    scope_id_b = str(uuid.uuid4())

    async with database_connection.begin_session_read_committed() as db_sess:
        for eid in (entity_id_1, entity_id_2):
            for sid in (scope_id_a, scope_id_b):
                db_sess.add(
                    ScopeUnbinderMappingRow(
                        id=uuid.uuid4(),
                        entity_id=eid,
                        scope_id=sid,
                    )
                )
                db_sess.add(
                    AssociationScopesEntitiesRow(
                        scope_type=ScopeType.DOMAIN,
                        scope_id=sid,
                        entity_type=EntityType.RESOURCE_GROUP,
                        entity_id=eid,
                    )
                )
        await db_sess.flush()

    yield UnbinderSeedContext(
        entity_id_1=entity_id_1,
        entity_id_2=entity_id_2,
        scope_id_a=scope_id_a,
        scope_id_b=scope_id_b,
    )


# =============================================================================
# Scope-Wide Entity Unbinder Tests
# =============================================================================


class TestRBACScopeEntityUnbinder:
    """Tests for scope entity unbinding (RBACScopeEntityUnbinder)."""

    async def test_unbind_single_entity_from_scope(
        self,
        database_connection: ExtendedAsyncSAEngine,
        seed_data: UnbinderSeedContext,
    ) -> None:
        """Unbinding one entity from scope_a removes that pair."""
        ctx = seed_data

        async with database_connection.begin_session_read_committed() as db_sess:
            unbinder = TestScopeEntityUnbinder(
                entity_ids=[ctx.entity_id_1],
                entity_element_type=RBACElementType.RESOURCE_GROUP,
                scope_id=ctx.scope_id_a,
                scope_element_type=RBACElementType.DOMAIN,
            )
            result = await execute_rbac_scope_entity_unbinder(db_sess, unbinder)

            assert isinstance(result, RBACUnbinderResult)
            assert result.deleted_count == 1
            assert len(result.association_rows) == 1

            # 3 mapping rows remain
            mapping_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ScopeUnbinderMappingRow)
            )
            assert mapping_count == 3

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 3

    async def test_unbind_multiple_entities_from_scope(
        self,
        database_connection: ExtendedAsyncSAEngine,
        seed_data: UnbinderSeedContext,
    ) -> None:
        """Unbinding both entities from scope_a removes both pairs in one call."""
        ctx = seed_data

        async with database_connection.begin_session_read_committed() as db_sess:
            unbinder = TestScopeEntityUnbinder(
                entity_ids=[ctx.entity_id_1, ctx.entity_id_2],
                entity_element_type=RBACElementType.RESOURCE_GROUP,
                scope_id=ctx.scope_id_a,
                scope_element_type=RBACElementType.DOMAIN,
            )
            result = await execute_rbac_scope_entity_unbinder(db_sess, unbinder)

            assert result.deleted_count == 2
            assert len(result.association_rows) == 2

            # 2 mapping rows remain (both entities x scope_b)
            mapping_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ScopeUnbinderMappingRow)
            )
            assert mapping_count == 2

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 2

    async def test_unbind_all_entities_from_scope(
        self,
        database_connection: ExtendedAsyncSAEngine,
        seed_data: UnbinderSeedContext,
    ) -> None:
        """When entity_ids is None, all entities of that type in the scope are removed."""
        ctx = seed_data

        async with database_connection.begin_session_read_committed() as db_sess:
            unbinder = TestScopeEntityUnbinder(
                entity_ids=None,
                entity_element_type=RBACElementType.RESOURCE_GROUP,
                scope_id=ctx.scope_id_a,
                scope_element_type=RBACElementType.DOMAIN,
            )
            result = await execute_rbac_scope_entity_unbinder(db_sess, unbinder)

            # Both entities in scope_a deleted
            assert result.deleted_count == 2
            assert len(result.association_rows) == 2

            # 2 mapping rows remain (both entities x scope_b)
            mapping_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ScopeUnbinderMappingRow)
            )
            assert mapping_count == 2

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 2

    async def test_unbind_entity_no_rows(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Unbinding a non-existent entity returns zero counts."""
        async with database_connection.begin_session_read_committed() as db_sess:
            unbinder = TestScopeEntityUnbinder(
                entity_ids=[str(uuid.uuid4())],
                entity_element_type=RBACElementType.RESOURCE_GROUP,
                scope_id=str(uuid.uuid4()),
                scope_element_type=RBACElementType.DOMAIN,
            )
            result = await execute_rbac_scope_entity_unbinder(db_sess, unbinder)

            assert result.deleted_count == 0
            assert len(result.association_rows) == 0

    async def test_unbind_all_entities_no_rows(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Unbinding all entities from a non-existent scope returns zero counts."""
        async with database_connection.begin_session_read_committed() as db_sess:
            unbinder = TestScopeEntityUnbinder(
                entity_ids=None,
                entity_element_type=RBACElementType.RESOURCE_GROUP,
                scope_id=str(uuid.uuid4()),
                scope_element_type=RBACElementType.DOMAIN,
            )
            result = await execute_rbac_scope_entity_unbinder(db_sess, unbinder)

            assert result.deleted_count == 0
            assert len(result.association_rows) == 0

    async def test_unbind_all_entities_preserves_other_scope(
        self,
        database_connection: ExtendedAsyncSAEngine,
        seed_data: UnbinderSeedContext,
    ) -> None:
        """After unbinding all entities from scope_a, scope_b associations remain intact."""
        ctx = seed_data

        async with database_connection.begin_session_read_committed() as db_sess:
            unbinder = TestScopeEntityUnbinder(
                entity_ids=None,
                entity_element_type=RBACElementType.RESOURCE_GROUP,
                scope_id=ctx.scope_id_a,
                scope_element_type=RBACElementType.DOMAIN,
            )
            await execute_rbac_scope_entity_unbinder(db_sess, unbinder)

            remaining = (await db_sess.scalars(sa.select(AssociationScopesEntitiesRow))).all()
            assert len(remaining) == 2
            # Only scope_b associations remain
            assert all(r.scope_id == ctx.scope_id_b for r in remaining)
            assert {r.entity_id for r in remaining} == {ctx.entity_id_1, ctx.entity_id_2}

    async def test_unbind_specific_entity_preserves_other_scope(
        self,
        database_connection: ExtendedAsyncSAEngine,
        seed_data: UnbinderSeedContext,
    ) -> None:
        """After unbinding entity_1 from scope_a, scope_b and entity_2 associations remain."""
        ctx = seed_data

        async with database_connection.begin_session_read_committed() as db_sess:
            unbinder = TestScopeEntityUnbinder(
                entity_ids=[ctx.entity_id_1],
                entity_element_type=RBACElementType.RESOURCE_GROUP,
                scope_id=ctx.scope_id_a,
                scope_element_type=RBACElementType.DOMAIN,
            )
            await execute_rbac_scope_entity_unbinder(db_sess, unbinder)

            remaining = (await db_sess.scalars(sa.select(AssociationScopesEntitiesRow))).all()
            assert len(remaining) == 3
            # entity_1 x scope_b, entity_2 x scope_a, entity_2 x scope_b remain
            entity1_remaining = [r for r in remaining if r.entity_id == ctx.entity_id_1]
            assert len(entity1_remaining) == 1
            assert entity1_remaining[0].scope_id == ctx.scope_id_b

            entity2_remaining = [r for r in remaining if r.entity_id == ctx.entity_id_2]
            assert len(entity2_remaining) == 2
            assert {r.scope_id for r in entity2_remaining} == {
                ctx.scope_id_a,
                ctx.scope_id_b,
            }
