"""Integration tests for RBAC scope unbinder with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

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
    RBACEntityUnbinder,
    RBACScopeUnbinder,
    RBACUnbinderResult,
    execute_rbac_entity_unbinder,
    execute_rbac_scope_unbinder,
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

    id: Mapped[UUID] = mapped_column(
        GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    entity_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    scope_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)


# =============================================================================
# Unbinder Implementations
# =============================================================================


class TestEntityUnbinder(RBACEntityUnbinder[ScopeUnbinderMappingRow]):
    """Entity unbinder: delete by entity, optionally filtered by scope."""

    def __init__(
        self,
        entity_id: str,
        entity_element_type: RBACElementType,
        scope_id: str | None = None,
        scope_element_type: RBACElementType | None = None,
    ) -> None:
        self._entity_id = entity_id
        self._entity_element_type = entity_element_type
        self._scope_id = scope_id
        self._scope_element_type = scope_element_type

    def build_purger_spec(self) -> BatchPurgerSpec[ScopeUnbinderMappingRow]:
        entity_id = self._entity_id
        scope_id = self._scope_id

        class _Spec(BatchPurgerSpec[ScopeUnbinderMappingRow]):
            def build_subquery(self) -> sa.sql.Select[tuple[ScopeUnbinderMappingRow]]:
                stmt = sa.select(ScopeUnbinderMappingRow).where(
                    ScopeUnbinderMappingRow.entity_id == entity_id,
                )
                if scope_id is not None:
                    stmt = stmt.where(ScopeUnbinderMappingRow.scope_id == scope_id)
                return stmt

        return _Spec()

    @property
    def entity_ref(self) -> RBACElementRef:
        return RBACElementRef(self._entity_element_type, self._entity_id)

    @property
    def scope_ref(self) -> RBACElementRef | None:
        if self._scope_id is None or self._scope_element_type is None:
            return None
        return RBACElementRef(self._scope_element_type, self._scope_id)


class TestScopeUnbinder(RBACScopeUnbinder[ScopeUnbinderMappingRow]):
    """Scope unbinder: delete by scope, optionally filtered by entity."""

    def __init__(
        self,
        scope_id: str,
        scope_element_type: RBACElementType,
        entity_id: str | None = None,
        entity_element_type: RBACElementType | None = None,
    ) -> None:
        self._scope_id = scope_id
        self._scope_element_type = scope_element_type
        self._entity_id = entity_id
        self._entity_element_type = entity_element_type

    def build_purger_spec(self) -> BatchPurgerSpec[ScopeUnbinderMappingRow]:
        scope_id = self._scope_id
        entity_id = self._entity_id

        class _Spec(BatchPurgerSpec[ScopeUnbinderMappingRow]):
            def build_subquery(self) -> sa.sql.Select[tuple[ScopeUnbinderMappingRow]]:
                stmt = sa.select(ScopeUnbinderMappingRow).where(
                    ScopeUnbinderMappingRow.scope_id == scope_id,
                )
                if entity_id is not None:
                    stmt = stmt.where(ScopeUnbinderMappingRow.entity_id == entity_id)
                return stmt

        return _Spec()

    @property
    def scope_ref(self) -> RBACElementRef:
        return RBACElementRef(self._scope_element_type, self._scope_id)

    @property
    def entity_ref(self) -> RBACElementRef | None:
        if self._entity_id is None or self._entity_element_type is None:
            return None
        return RBACElementRef(self._entity_element_type, self._entity_id)


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
# Entity Unbinder Tests
# =============================================================================


class TestRBACEntityUnbinder:
    """Tests for entity-centric unbinding (RBACEntityUnbinder)."""

    async def test_unbind_entity_from_all_scopes(
        self,
        database_connection: ExtendedAsyncSAEngine,
        seed_data: UnbinderSeedContext,
    ) -> None:
        """Unbinding entity_1 with scope_ref=None removes all its mappings/associations."""
        ctx = seed_data

        async with database_connection.begin_session_read_committed() as db_sess:
            unbinder = TestEntityUnbinder(
                entity_id=ctx.entity_id_1,
                entity_element_type=RBACElementType.RESOURCE_GROUP,
            )
            result = await execute_rbac_entity_unbinder(db_sess, unbinder)

            assert isinstance(result, RBACUnbinderResult)
            assert result.deleted_count == 2  # 2 mapping rows for entity_1
            assert len(result.association_rows) == 2  # 2 assoc rows for entity_1

            # entity_2 mappings remain
            mapping_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ScopeUnbinderMappingRow)
            )
            assert mapping_count == 2

            # entity_2 associations remain
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 2

    async def test_unbind_entity_from_specific_scope(
        self,
        database_connection: ExtendedAsyncSAEngine,
        seed_data: UnbinderSeedContext,
    ) -> None:
        """Unbinding entity_1 from scope_a removes only that pair."""
        ctx = seed_data

        async with database_connection.begin_session_read_committed() as db_sess:
            unbinder = TestEntityUnbinder(
                entity_id=ctx.entity_id_1,
                entity_element_type=RBACElementType.RESOURCE_GROUP,
                scope_id=ctx.scope_id_a,
                scope_element_type=RBACElementType.DOMAIN,
            )
            result = await execute_rbac_entity_unbinder(db_sess, unbinder)

            assert result.deleted_count == 1
            assert len(result.association_rows) == 1

            # 3 mapping rows remain (entity_1×scope_b, entity_2×scope_a, entity_2×scope_b)
            mapping_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ScopeUnbinderMappingRow)
            )
            assert mapping_count == 3

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 3

    async def test_unbind_entity_no_rows(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Unbinding a non-existent entity returns zero counts."""
        async with database_connection.begin_session_read_committed() as db_sess:
            unbinder = TestEntityUnbinder(
                entity_id=str(uuid.uuid4()),
                entity_element_type=RBACElementType.RESOURCE_GROUP,
            )
            result = await execute_rbac_entity_unbinder(db_sess, unbinder)

            assert result.deleted_count == 0
            assert len(result.association_rows) == 0


# =============================================================================
# Scope Unbinder Tests
# =============================================================================


class TestRBACScopeUnbinder:
    """Tests for scope-centric unbinding (RBACScopeUnbinder)."""

    async def test_unbind_scope_from_all_entities(
        self,
        database_connection: ExtendedAsyncSAEngine,
        seed_data: UnbinderSeedContext,
    ) -> None:
        """Unbinding scope_a with entity_ref=None removes all its mappings/associations."""
        ctx = seed_data

        async with database_connection.begin_session_read_committed() as db_sess:
            unbinder = TestScopeUnbinder(
                scope_id=ctx.scope_id_a,
                scope_element_type=RBACElementType.DOMAIN,
            )
            result = await execute_rbac_scope_unbinder(db_sess, unbinder)

            assert isinstance(result, RBACUnbinderResult)
            assert result.deleted_count == 2  # 2 mapping rows for scope_a
            assert len(result.association_rows) == 2  # 2 assoc rows for scope_a

            # scope_b mappings remain
            mapping_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ScopeUnbinderMappingRow)
            )
            assert mapping_count == 2

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 2

    async def test_unbind_scope_from_specific_entity(
        self,
        database_connection: ExtendedAsyncSAEngine,
        seed_data: UnbinderSeedContext,
    ) -> None:
        """Unbinding scope_a from entity_1 removes only that pair."""
        ctx = seed_data

        async with database_connection.begin_session_read_committed() as db_sess:
            unbinder = TestScopeUnbinder(
                scope_id=ctx.scope_id_a,
                scope_element_type=RBACElementType.DOMAIN,
                entity_id=ctx.entity_id_1,
                entity_element_type=RBACElementType.RESOURCE_GROUP,
            )
            result = await execute_rbac_scope_unbinder(db_sess, unbinder)

            assert result.deleted_count == 1
            assert len(result.association_rows) == 1

            mapping_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ScopeUnbinderMappingRow)
            )
            assert mapping_count == 3

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 3

    async def test_unbind_scope_no_rows(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Unbinding a non-existent scope returns zero counts."""
        async with database_connection.begin_session_read_committed() as db_sess:
            unbinder = TestScopeUnbinder(
                scope_id=str(uuid.uuid4()),
                scope_element_type=RBACElementType.DOMAIN,
            )
            result = await execute_rbac_scope_unbinder(db_sess, unbinder)

            assert result.deleted_count == 0
            assert len(result.association_rows) == 0

    async def test_unbind_scope_preserves_other_scope(
        self,
        database_connection: ExtendedAsyncSAEngine,
        seed_data: UnbinderSeedContext,
    ) -> None:
        """After unbinding scope_a, scope_b associations are intact."""
        ctx = seed_data

        async with database_connection.begin_session_read_committed() as db_sess:
            unbinder = TestScopeUnbinder(
                scope_id=ctx.scope_id_a,
                scope_element_type=RBACElementType.DOMAIN,
            )
            await execute_rbac_scope_unbinder(db_sess, unbinder)

            remaining = (await db_sess.scalars(sa.select(AssociationScopesEntitiesRow))).all()
            assert all(row.scope_id == ctx.scope_id_b for row in remaining)
            assert len(remaining) == 2
