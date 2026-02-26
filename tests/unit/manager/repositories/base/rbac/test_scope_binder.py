"""Integration tests for RBAC scope binder with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.common.data.permission.types import RelationType
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
from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.repositories.base.rbac.scope_binder import (
    RBACScopeBinder,
    RBACScopeBinderResult,
    RBACScopeBindingPair,
    execute_rbac_scope_binder,
)
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


# =============================================================================
# Test Row Model (N:N mapping table)
# =============================================================================


class ScopeBinderMappingRow(Base):  # type: ignore[misc]
    """N:N mapping row for scope binder testing."""

    __tablename__ = "test_scope_binder_mapping"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(
        GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    entity_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    scope_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)


# =============================================================================
# CreatorSpec Implementation
# =============================================================================


class MappingCreatorSpec(CreatorSpec[ScopeBinderMappingRow]):
    """Creates a single N:N mapping row."""

    def __init__(self, entity_id: str, scope_id: str) -> None:
        self._entity_id = entity_id
        self._scope_id = scope_id

    def build_row(self) -> ScopeBinderMappingRow:
        return ScopeBinderMappingRow(
            id=uuid.uuid4(),
            entity_id=self._entity_id,
            scope_id=self._scope_id,
        )


# =============================================================================
# Helpers
# =============================================================================


def make_binding_pair(
    entity_id: str,
    scope_id: str,
    relation_type: RelationType = RelationType.AUTO,
) -> RBACScopeBindingPair[ScopeBinderMappingRow]:
    return RBACScopeBindingPair(
        spec=MappingCreatorSpec(entity_id=entity_id, scope_id=scope_id),
        entity_ref=RBACElementRef(RBACElementType.RESOURCE_GROUP, entity_id),
        scope_ref=RBACElementRef(RBACElementType.DOMAIN, scope_id),
        relation_type=relation_type,
    )


# =============================================================================
# Tables & Fixtures
# =============================================================================

BINDER_TABLES = [
    ScopeBinderMappingRow,
    AssociationScopesEntitiesRow,
]


@pytest.fixture
async def create_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    async with with_tables(database_connection, BINDER_TABLES):  # type: ignore[arg-type]
        yield


@pytest.fixture
def entity_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def entity_id_2() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def scope_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def scope_id_b() -> str:
    return str(uuid.uuid4())


@dataclass
class PreBoundContext:
    """Context after pre-binding entity to scope_a."""

    entity_id: str
    scope_id_a: str
    scope_id_b: str


@pytest.fixture
async def pre_bound_scope_a(
    database_connection: ExtendedAsyncSAEngine,
    create_tables: None,
    entity_id: str,
    scope_id: str,
    scope_id_b: str,
) -> AsyncGenerator[PreBoundContext, None]:
    """Pre-bind entity to scope (used as scope_a) so the association already exists."""
    async with database_connection.begin_session_read_committed() as db_sess:
        binder: RBACScopeBinder[ScopeBinderMappingRow] = RBACScopeBinder(
            pairs=[make_binding_pair(entity_id, scope_id)],
        )
        await execute_rbac_scope_binder(db_sess, binder)

    yield PreBoundContext(
        entity_id=entity_id,
        scope_id_a=scope_id,
        scope_id_b=scope_id_b,
    )


# =============================================================================
# Tests
# =============================================================================


class TestRBACScopeBinderBasic:
    """Basic tests for scope binder operations."""

    async def test_bind_single_pair(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        scope_id: str,
    ) -> None:
        """Single pair creates 1 mapping row + 1 association row."""
        async with database_connection.begin_session_read_committed() as db_sess:
            binder: RBACScopeBinder[ScopeBinderMappingRow] = RBACScopeBinder(
                pairs=[make_binding_pair(entity_id, scope_id)],
            )
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert isinstance(result, RBACScopeBinderResult)
            assert len(result.rows) == 1
            assert result.rows[0].entity_id == entity_id
            assert result.rows[0].scope_id == scope_id
            assert len(result.association_rows) == 1

            assoc = result.association_rows[0]
            assert assoc.entity_type == EntityType.RESOURCE_GROUP
            assert assoc.entity_id == entity_id
            assert assoc.scope_type == ScopeType.DOMAIN
            assert assoc.scope_id == scope_id
            assert assoc.relation_type == RelationType.AUTO

    async def test_bind_multiple_pairs(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        entity_id_2: str,
        scope_id: str,
    ) -> None:
        """Multiple pairs create corresponding mapping + association rows."""
        async with database_connection.begin_session_read_committed() as db_sess:
            binder: RBACScopeBinder[ScopeBinderMappingRow] = RBACScopeBinder(
                pairs=[
                    make_binding_pair(entity_id, scope_id),
                    make_binding_pair(entity_id_2, scope_id),
                ],
            )
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert len(result.rows) == 2
            assert len(result.association_rows) == 2

            mapping_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ScopeBinderMappingRow)
            )
            assert mapping_count == 2

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 2

    async def test_bind_empty_pairs(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Empty pairs list returns empty result without DB writes."""
        async with database_connection.begin_session_read_committed() as db_sess:
            binder: RBACScopeBinder[ScopeBinderMappingRow] = RBACScopeBinder(pairs=[])
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert isinstance(result, RBACScopeBinderResult)
            assert len(result.rows) == 0
            assert len(result.association_rows) == 0

            mapping_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ScopeBinderMappingRow)
            )
            assert mapping_count == 0


class TestRBACScopeBinderRelationType:
    """Tests for relation_type handling."""

    async def test_default_relation_type_is_auto(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        scope_id: str,
    ) -> None:
        """Default relation_type is AUTO."""
        async with database_connection.begin_session_read_committed() as db_sess:
            binder: RBACScopeBinder[ScopeBinderMappingRow] = RBACScopeBinder(
                pairs=[make_binding_pair(entity_id, scope_id)],
            )
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert result.association_rows[0].relation_type == RelationType.AUTO

    async def test_explicit_ref_relation_type(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        scope_id: str,
    ) -> None:
        """Explicit REF relation_type is stored correctly."""
        async with database_connection.begin_session_read_committed() as db_sess:
            binder: RBACScopeBinder[ScopeBinderMappingRow] = RBACScopeBinder(
                pairs=[make_binding_pair(entity_id, scope_id, relation_type=RelationType.REF)],
            )
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert result.association_rows[0].relation_type == RelationType.REF


class TestRBACScopeBinderIdempotent:
    """Tests for idempotent association handling (ON CONFLICT DO NOTHING)."""

    async def test_duplicate_association_is_idempotent(
        self,
        database_connection: ExtendedAsyncSAEngine,
        pre_bound_scope_a: PreBoundContext,
    ) -> None:
        """Binding the same entity+scope again creates a new mapping row but no new association."""
        ctx = pre_bound_scope_a

        async with database_connection.begin_session_read_committed() as db_sess:
            binder: RBACScopeBinder[ScopeBinderMappingRow] = RBACScopeBinder(
                pairs=[make_binding_pair(ctx.entity_id, ctx.scope_id_a)],
            )
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert len(result.rows) == 1
            assert len(result.association_rows) == 0

            # Total: 2 mapping rows, 1 association
            mapping_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ScopeBinderMappingRow)
            )
            assert mapping_count == 2

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 1

    async def test_mixed_new_and_existing_associations(
        self,
        database_connection: ExtendedAsyncSAEngine,
        pre_bound_scope_a: PreBoundContext,
    ) -> None:
        """Batch with both new and existing associations handles correctly."""
        ctx = pre_bound_scope_a

        async with database_connection.begin_session_read_committed() as db_sess:
            binder: RBACScopeBinder[ScopeBinderMappingRow] = RBACScopeBinder(
                pairs=[
                    make_binding_pair(ctx.entity_id, ctx.scope_id_a),
                    make_binding_pair(ctx.entity_id, ctx.scope_id_b),
                ],
            )
            result = await execute_rbac_scope_binder(db_sess, binder)

            # 2 mapping rows created, but only scope_b association is new
            assert len(result.rows) == 2
            assert len(result.association_rows) == 1
            assert result.association_rows[0].scope_id == ctx.scope_id_b

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 2
