"""Integration tests for RBAC scope binder/unbinder with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Sequence
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from ai.backend.manager.data.permission.types import (
    EntityType,
    RBACElementRef,
    RBACElementType,
    RelationType,
    ScopeType,
)
from ai.backend.manager.models.base import GUID, Base
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.repositories.base.purger import BatchPurgerSpec
from ai.backend.manager.repositories.base.rbac.scope_binder import (
    RBACScopeBinder,
    RBACScopeBinderResult,
    RBACScopeBindingPair,
    RBACScopeUnbinder,
    RBACScopeUnbinderResult,
    execute_rbac_scope_binder,
    execute_rbac_scope_unbinder,
)
from ai.backend.manager.repositories.base.types import IntegrityErrorCheck
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


# =============================================================================
# Test N:N Mapping Row
# =============================================================================


class ScopeBinderMappingRow(Base):  # type: ignore[misc]
    """Simple N:N mapping row for scope binder testing.

    Represents a mapping like sgroups_for_domains (entity_id <-> scope_id).
    """

    __tablename__ = "test_scope_binder_mapping"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, server_default=sa.text("uuid_generate_v4()")
    )
    entity_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)
    scope_id: Mapped[str] = mapped_column(sa.String(64), nullable=False)


# =============================================================================
# CreatorSpec / BatchPurgerSpec
# =============================================================================


class MappingCreatorSpec(CreatorSpec[ScopeBinderMappingRow]):
    """CreatorSpec for the test N:N mapping row."""

    def __init__(self, entity_id: str, scope_id: str) -> None:
        self._entity_id = entity_id
        self._scope_id = scope_id

    @property
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    def build_row(self) -> ScopeBinderMappingRow:
        return ScopeBinderMappingRow(
            entity_id=self._entity_id,
            scope_id=self._scope_id,
        )


class MappingBatchPurgerSpec(BatchPurgerSpec[ScopeBinderMappingRow]):
    """BatchPurgerSpec for the test N:N mapping row."""

    def __init__(
        self,
        entity_id: str,
        scope_id: str,
    ) -> None:
        self._entity_id = entity_id
        self._scope_id = scope_id

    def build_subquery(self) -> sa.sql.Select[tuple[ScopeBinderMappingRow]]:
        return sa.select(ScopeBinderMappingRow).where(
            sa.and_(
                ScopeBinderMappingRow.entity_id == self._entity_id,
                ScopeBinderMappingRow.scope_id == self._scope_id,
            )
        )


# =============================================================================
# Tables & Fixtures
# =============================================================================

SCOPE_BINDER_TABLES = [
    ScopeBinderMappingRow,
    AssociationScopesEntitiesRow,
]


@pytest.fixture
async def create_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    async with with_tables(database_connection, SCOPE_BINDER_TABLES):  # type: ignore[arg-type]
        yield


@pytest.fixture
def entity_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def project_id_1() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def project_id_2() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def project_id_3() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def domain_id() -> str:
    return str(uuid.uuid4())


# =============================================================================
# Helper
# =============================================================================


def _make_binding(
    entity_type: RBACElementType,
    entity_id: str,
    scope_type: RBACElementType,
    scope_id: str,
    relation_type: RelationType = RelationType.AUTO,
) -> RBACScopeBindingPair:
    return RBACScopeBindingPair(
        entity_ref=RBACElementRef(entity_type, entity_id),
        scope_ref=RBACElementRef(scope_type, scope_id),
        relation_type=relation_type,
    )


# =============================================================================
# Binder Tests
# =============================================================================


class TestRBACScopeBinder:
    async def test_bind_single_pair(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_id_1: str,
    ) -> None:
        """Bind one mapping row + one RBAC association."""

        binder = RBACScopeBinder(
            specs=[MappingCreatorSpec(entity_id, project_id_1)],
            bindings=[
                _make_binding(
                    RBACElementType.CONTAINER_REGISTRY,
                    entity_id,
                    RBACElementType.PROJECT,
                    project_id_1,
                ),
            ],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert isinstance(result, RBACScopeBinderResult)
            # Business row
            assert len(result.rows) == 1
            assert result.rows[0].entity_id == entity_id
            assert result.rows[0].scope_id == project_id_1
            # RBAC association
            assert len(result.association_rows) == 1
            assoc = result.association_rows[0]
            assert assoc.scope_type == ScopeType.PROJECT
            assert assoc.scope_id == project_id_1
            assert assoc.entity_type == EntityType.CONTAINER_REGISTRY
            assert assoc.entity_id == entity_id
            assert assoc.relation_type == RelationType.AUTO

    async def test_bind_multiple_entities_one_scope(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        project_id_1: str,
    ) -> None:
        """Multiple entities -> 1 scope (e.g., AssociateScalingGroupsWithDomain)."""

        sg1 = str(uuid.uuid4())
        sg2 = str(uuid.uuid4())

        binder = RBACScopeBinder(
            specs=[
                MappingCreatorSpec(sg1, project_id_1),
                MappingCreatorSpec(sg2, project_id_1),
            ],
            bindings=[
                _make_binding(
                    RBACElementType.RESOURCE_GROUP,
                    sg1,
                    RBACElementType.PROJECT,
                    project_id_1,
                ),
                _make_binding(
                    RBACElementType.RESOURCE_GROUP,
                    sg2,
                    RBACElementType.PROJECT,
                    project_id_1,
                ),
            ],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert len(result.rows) == 2
            assert len(result.association_rows) == 2
            assoc_entity_ids = {r.entity_id for r in result.association_rows}
            assert assoc_entity_ids == {sg1, sg2}

    async def test_bind_one_entity_multiple_scopes(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_id_1: str,
        project_id_2: str,
    ) -> None:
        """1 entity -> multiple scopes (e.g., container registry -> groups)."""

        binder = RBACScopeBinder(
            specs=[
                MappingCreatorSpec(entity_id, project_id_1),
                MappingCreatorSpec(entity_id, project_id_2),
            ],
            bindings=[
                _make_binding(
                    RBACElementType.CONTAINER_REGISTRY,
                    entity_id,
                    RBACElementType.PROJECT,
                    project_id_1,
                ),
                _make_binding(
                    RBACElementType.CONTAINER_REGISTRY,
                    entity_id,
                    RBACElementType.PROJECT,
                    project_id_2,
                ),
            ],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert len(result.rows) == 2
            assert len(result.association_rows) == 2
            assoc_scope_ids = {r.scope_id for r in result.association_rows}
            assert assoc_scope_ids == {project_id_1, project_id_2}

    async def test_bind_duplicate_association_returns_empty(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_id_1: str,
    ) -> None:
        """Duplicate RBAC binding returns no association rows (ON CONFLICT DO NOTHING)."""

        binding = _make_binding(
            RBACElementType.CONTAINER_REGISTRY,
            entity_id,
            RBACElementType.PROJECT,
            project_id_1,
        )

        # First bind
        async with database_connection.begin_session() as db_sess:
            binder1 = RBACScopeBinder(
                specs=[MappingCreatorSpec(entity_id, project_id_1)],
                bindings=[binding],
            )
            first = await execute_rbac_scope_binder(db_sess, binder1)
            assert len(first.association_rows) == 1

        # Second bind (no specs to avoid duplicate mapping row, only bindings)
        async with database_connection.begin_session() as db_sess:
            binder2: RBACScopeBinder[ScopeBinderMappingRow] = RBACScopeBinder(
                specs=[],
                bindings=[binding],
            )
            second = await execute_rbac_scope_binder(db_sess, binder2)
            assert len(second.rows) == 0
            assert len(second.association_rows) == 0

            total = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert total == 1

    async def test_bind_with_per_pair_relation_type(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_id_1: str,
        project_id_2: str,
    ) -> None:
        """Each binding pair can carry its own relation_type."""

        binder = RBACScopeBinder(
            specs=[
                MappingCreatorSpec(entity_id, project_id_1),
                MappingCreatorSpec(entity_id, project_id_2),
            ],
            bindings=[
                _make_binding(
                    RBACElementType.CONTAINER_REGISTRY,
                    entity_id,
                    RBACElementType.PROJECT,
                    project_id_1,
                    relation_type=RelationType.AUTO,
                ),
                _make_binding(
                    RBACElementType.CONTAINER_REGISTRY,
                    entity_id,
                    RBACElementType.PROJECT,
                    project_id_2,
                    relation_type=RelationType.REF,
                ),
            ],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert len(result.association_rows) == 2
            relation_map = {r.scope_id: r.relation_type for r in result.association_rows}
            assert relation_map[project_id_1] == RelationType.AUTO
            assert relation_map[project_id_2] == RelationType.REF

    async def test_bind_empty_specs_and_bindings(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
    ) -> None:
        """Empty binder returns empty result without DB access."""

        binder: RBACScopeBinder[ScopeBinderMappingRow] = RBACScopeBinder(specs=[], bindings=[])

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_binder(db_sess, binder)
            assert result.rows == []
            assert result.association_rows == []

    async def test_bind_only_bindings_no_specs(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_id_1: str,
    ) -> None:
        """Bindings-only binder creates RBAC associations without business rows."""

        binder: RBACScopeBinder[ScopeBinderMappingRow] = RBACScopeBinder(
            specs=[],
            bindings=[
                _make_binding(
                    RBACElementType.CONTAINER_REGISTRY,
                    entity_id,
                    RBACElementType.PROJECT,
                    project_id_1,
                ),
            ],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_binder(db_sess, binder)
            assert result.rows == []
            assert len(result.association_rows) == 1

    async def test_bind_mixed_existing_and_new_associations(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_id_1: str,
        project_id_2: str,
        project_id_3: str,
    ) -> None:
        """When binding a mix of existing and new, only new associations are returned."""

        # Pre-bind project 1
        async with database_connection.begin_session() as db_sess:
            db_sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.PROJECT,
                    scope_id=project_id_1,
                    entity_type=EntityType.CONTAINER_REGISTRY,
                    entity_id=entity_id,
                )
            )
            await db_sess.flush()

        # Bind project 1 (existing) + project 2 & 3 (new)
        binder: RBACScopeBinder[ScopeBinderMappingRow] = RBACScopeBinder(
            specs=[],
            bindings=[
                _make_binding(
                    RBACElementType.CONTAINER_REGISTRY,
                    entity_id,
                    RBACElementType.PROJECT,
                    project_id_1,
                ),
                _make_binding(
                    RBACElementType.CONTAINER_REGISTRY,
                    entity_id,
                    RBACElementType.PROJECT,
                    project_id_2,
                ),
                _make_binding(
                    RBACElementType.CONTAINER_REGISTRY,
                    entity_id,
                    RBACElementType.PROJECT,
                    project_id_3,
                ),
            ],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert len(result.association_rows) == 2
            returned_scope_ids = {row.scope_id for row in result.association_rows}
            assert returned_scope_ids == {project_id_2, project_id_3}

            total = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert total == 3


# =============================================================================
# Unbinder Tests
# =============================================================================


class TestRBACScopeUnbinder:
    @pytest.fixture
    async def bound_pair(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_id_1: str,
    ) -> None:
        """Seed one mapping row + one RBAC association."""
        async with database_connection.begin_session() as db_sess:
            db_sess.add(ScopeBinderMappingRow(entity_id=entity_id, scope_id=project_id_1))
            db_sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.PROJECT,
                    scope_id=project_id_1,
                    entity_type=EntityType.CONTAINER_REGISTRY,
                    entity_id=entity_id,
                )
            )
            await db_sess.flush()

    @pytest.fixture
    async def two_bound_pairs(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_id_1: str,
        project_id_2: str,
    ) -> None:
        """Seed two mapping rows + two RBAC associations."""
        async with database_connection.begin_session() as db_sess:
            for pid in [project_id_1, project_id_2]:
                db_sess.add(ScopeBinderMappingRow(entity_id=entity_id, scope_id=pid))
                db_sess.add(
                    AssociationScopesEntitiesRow(
                        scope_type=ScopeType.PROJECT,
                        scope_id=pid,
                        entity_type=EntityType.CONTAINER_REGISTRY,
                        entity_id=entity_id,
                    )
                )
            await db_sess.flush()

    async def test_unbind_single_pair(
        self,
        database_connection: ExtendedAsyncSAEngine,
        bound_pair: None,
        entity_id: str,
        project_id_1: str,
    ) -> None:
        """Unbind deletes both the business row and the RBAC association."""

        unbinder = RBACScopeUnbinder(
            purger_spec=MappingBatchPurgerSpec(entity_id, project_id_1),
            bindings=[
                _make_binding(
                    RBACElementType.CONTAINER_REGISTRY,
                    entity_id,
                    RBACElementType.PROJECT,
                    project_id_1,
                ),
            ],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_unbinder(db_sess, unbinder)

            assert isinstance(result, RBACScopeUnbinderResult)
            assert result.deleted_count == 1
            assert len(result.association_rows) == 1
            assert result.association_rows[0].scope_id == project_id_1

            # Verify both tables are empty
            mapping_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(ScopeBinderMappingRow)
            )
            assert mapping_count == 0

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 0

    async def test_unbind_one_of_two(
        self,
        database_connection: ExtendedAsyncSAEngine,
        two_bound_pairs: None,
        entity_id: str,
        project_id_1: str,
        project_id_2: str,
    ) -> None:
        """Unbinding one pair preserves the other."""

        unbinder = RBACScopeUnbinder(
            purger_spec=MappingBatchPurgerSpec(entity_id, project_id_1),
            bindings=[
                _make_binding(
                    RBACElementType.CONTAINER_REGISTRY,
                    entity_id,
                    RBACElementType.PROJECT,
                    project_id_1,
                ),
            ],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_unbinder(db_sess, unbinder)

            assert result.deleted_count == 1
            assert len(result.association_rows) == 1

            # One mapping row and one association should remain
            remaining_mappings = (await db_sess.scalars(sa.select(ScopeBinderMappingRow))).all()
            assert len(remaining_mappings) == 1
            assert remaining_mappings[0].scope_id == project_id_2

            remaining_assocs = (
                await db_sess.scalars(sa.select(AssociationScopesEntitiesRow))
            ).all()
            assert len(remaining_assocs) == 1
            assert remaining_assocs[0].scope_id == project_id_2

    async def test_unbind_nonexistent_returns_zero(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_id_1: str,
    ) -> None:
        """Unbinding non-existent pairs returns zero counts and empty lists."""

        unbinder = RBACScopeUnbinder(
            purger_spec=MappingBatchPurgerSpec(entity_id, project_id_1),
            bindings=[
                _make_binding(
                    RBACElementType.CONTAINER_REGISTRY,
                    entity_id,
                    RBACElementType.PROJECT,
                    project_id_1,
                ),
            ],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_unbinder(db_sess, unbinder)
            assert result.deleted_count == 0
            assert result.association_rows == []

    async def test_unbind_empty_bindings(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_id_1: str,
    ) -> None:
        """Empty bindings returns early with zero counts."""

        unbinder = RBACScopeUnbinder(
            purger_spec=MappingBatchPurgerSpec(entity_id, project_id_1),
            bindings=[],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_unbinder(db_sess, unbinder)
            assert result.deleted_count == 0
            assert result.association_rows == []

    async def test_unbind_preserves_other_entities_associations(
        self,
        database_connection: ExtendedAsyncSAEngine,
        bound_pair: None,
        entity_id: str,
        project_id_1: str,
    ) -> None:
        """Unbinding only removes the target entity's association, not others'."""

        other_entity_id = str(uuid.uuid4())

        # Add another entity's association on the same scope
        async with database_connection.begin_session() as db_sess:
            db_sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.PROJECT,
                    scope_id=project_id_1,
                    entity_type=EntityType.CONTAINER_REGISTRY,
                    entity_id=other_entity_id,
                )
            )
            await db_sess.flush()

        unbinder = RBACScopeUnbinder(
            purger_spec=MappingBatchPurgerSpec(entity_id, project_id_1),
            bindings=[
                _make_binding(
                    RBACElementType.CONTAINER_REGISTRY,
                    entity_id,
                    RBACElementType.PROJECT,
                    project_id_1,
                ),
            ],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_unbinder(db_sess, unbinder)

            assert result.deleted_count == 1
            assert len(result.association_rows) == 1
            assert result.association_rows[0].entity_id == entity_id

            # Other entity's association still exists
            remaining = (await db_sess.scalars(sa.select(AssociationScopesEntitiesRow))).all()
            assert len(remaining) == 1
            assert remaining[0].entity_id == other_entity_id

    async def test_unbind_with_mixed_scope_types(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_id_1: str,
        domain_id: str,
    ) -> None:
        """Unbind can target different scope types in one call."""

        # Seed: one PROJECT and one DOMAIN association
        async with database_connection.begin_session() as db_sess:
            db_sess.add(ScopeBinderMappingRow(entity_id=entity_id, scope_id=project_id_1))
            db_sess.add(ScopeBinderMappingRow(entity_id=entity_id, scope_id=domain_id))
            db_sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.PROJECT,
                    scope_id=project_id_1,
                    entity_type=EntityType.RESOURCE_GROUP,
                    entity_id=entity_id,
                )
            )
            db_sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.DOMAIN,
                    scope_id=domain_id,
                    entity_type=EntityType.RESOURCE_GROUP,
                    entity_id=entity_id,
                )
            )
            await db_sess.flush()

        # Unbind the project association only
        unbinder = RBACScopeUnbinder(
            purger_spec=MappingBatchPurgerSpec(entity_id, project_id_1),
            bindings=[
                _make_binding(
                    RBACElementType.RESOURCE_GROUP,
                    entity_id,
                    RBACElementType.PROJECT,
                    project_id_1,
                ),
                _make_binding(
                    RBACElementType.RESOURCE_GROUP,
                    entity_id,
                    RBACElementType.DOMAIN,
                    domain_id,
                ),
            ],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_unbinder(db_sess, unbinder)

            assert len(result.association_rows) == 2
            returned_scope_types = {row.scope_type for row in result.association_rows}
            assert ScopeType.PROJECT in returned_scope_types
            assert ScopeType.DOMAIN in returned_scope_types
