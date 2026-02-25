"""Integration tests for RBAC scope binder with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa

from ai.backend.manager.data.permission.types import (
    EntityType,
    RBACElementRef,
    RBACElementType,
    RelationType,
    ScopeType,
)
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.repositories.base.rbac.scope_binder import (
    RBACScopeBinder,
    RBACScopeBinderResult,
    execute_rbac_scope_binder,
)
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


# =============================================================================
# Tables List
# =============================================================================

SCOPE_BINDER_TABLES = [
    AssociationScopesEntitiesRow,
]


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def create_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    """Create RBAC scope binder test tables."""
    async with with_tables(database_connection, SCOPE_BINDER_TABLES):
        yield


@pytest.fixture
def entity_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def project_scope_id_1() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def project_scope_id_2() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def project_scope_id_3() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def domain_scope_id() -> str:
    return str(uuid.uuid4())


# =============================================================================
# Bind Tests
# =============================================================================


class TestRBACScopeBinderBind:
    """Tests for binding (inserting) scope associations."""

    async def test_bind_single_scope(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_scope_id_1: str,
    ) -> None:
        """Test binding a single scope to an entity."""
        binder = RBACScopeBinder(
            element_type=RBACElementType.CONTAINER_REGISTRY,
            entity_id=entity_id,
            bind_scope_refs=[
                RBACElementRef(RBACElementType.PROJECT, project_scope_id_1),
            ],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert isinstance(result, RBACScopeBinderResult)
            assert result.bound_count == 1
            assert result.unbound_count == 0

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 1

            assoc_row = await db_sess.scalar(sa.select(AssociationScopesEntitiesRow))
            assert assoc_row is not None
            assert assoc_row.scope_type == ScopeType.PROJECT
            assert assoc_row.scope_id == project_scope_id_1
            assert assoc_row.entity_type == EntityType.CONTAINER_REGISTRY
            assert assoc_row.entity_id == entity_id
            assert assoc_row.relation_type == RelationType.AUTO

    async def test_bind_multiple_scopes(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_scope_id_1: str,
        project_scope_id_2: str,
        project_scope_id_3: str,
    ) -> None:
        """Test binding multiple scopes to an entity."""
        binder = RBACScopeBinder(
            element_type=RBACElementType.CONTAINER_REGISTRY,
            entity_id=entity_id,
            bind_scope_refs=[
                RBACElementRef(RBACElementType.PROJECT, project_scope_id_1),
                RBACElementRef(RBACElementType.PROJECT, project_scope_id_2),
                RBACElementRef(RBACElementType.PROJECT, project_scope_id_3),
            ],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert result.bound_count == 3
            assert result.unbound_count == 0

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 3

    async def test_bind_duplicate_scope_is_idempotent(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_scope_id_1: str,
    ) -> None:
        """Test that binding an already-bound scope does not create duplicates."""
        binder = RBACScopeBinder(
            element_type=RBACElementType.CONTAINER_REGISTRY,
            entity_id=entity_id,
            bind_scope_refs=[
                RBACElementRef(RBACElementType.PROJECT, project_scope_id_1),
            ],
        )

        async with database_connection.begin_session() as db_sess:
            await execute_rbac_scope_binder(db_sess, binder)

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert result.bound_count == 0

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 1

    async def test_bind_with_custom_relation_type(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_scope_id_1: str,
    ) -> None:
        """Test binding with a non-default relation type."""
        binder = RBACScopeBinder(
            element_type=RBACElementType.CONTAINER_REGISTRY,
            entity_id=entity_id,
            bind_scope_refs=[
                RBACElementRef(RBACElementType.PROJECT, project_scope_id_1),
            ],
            relation_type=RelationType.REF,
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert result.bound_count == 1

            assoc_row = await db_sess.scalar(sa.select(AssociationScopesEntitiesRow))
            assert assoc_row is not None
            assert assoc_row.relation_type == RelationType.REF

    async def test_bind_empty_scope_refs(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
    ) -> None:
        """Test binding with empty scope refs is a no-op."""
        binder = RBACScopeBinder(
            element_type=RBACElementType.CONTAINER_REGISTRY,
            entity_id=entity_id,
            bind_scope_refs=[],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert result.bound_count == 0
            assert result.unbound_count == 0

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 0


# =============================================================================
# Unbind Tests
# =============================================================================


class TestRBACScopeBinderUnbind:
    """Tests for unbinding (deleting) scope associations."""

    async def test_unbind_single_scope(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_scope_id_1: str,
        project_scope_id_2: str,
    ) -> None:
        """Test unbinding a single scope from an entity."""
        # Setup: bind two scopes first
        async with database_connection.begin_session() as db_sess:
            for scope_id in [project_scope_id_1, project_scope_id_2]:
                db_sess.add(
                    AssociationScopesEntitiesRow(
                        scope_type=ScopeType.PROJECT,
                        scope_id=scope_id,
                        entity_type=EntityType.CONTAINER_REGISTRY,
                        entity_id=entity_id,
                    )
                )
            await db_sess.flush()

        # Unbind one scope
        binder = RBACScopeBinder(
            element_type=RBACElementType.CONTAINER_REGISTRY,
            entity_id=entity_id,
            unbind_scope_refs=[
                RBACElementRef(RBACElementType.PROJECT, project_scope_id_1),
            ],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert result.unbound_count == 1
            assert result.bound_count == 0

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 1

            remaining = await db_sess.scalar(sa.select(AssociationScopesEntitiesRow))
            assert remaining is not None
            assert remaining.scope_id == project_scope_id_2

    async def test_unbind_all_scopes(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_scope_id_1: str,
        project_scope_id_2: str,
    ) -> None:
        """Test unbinding all scopes from an entity."""
        async with database_connection.begin_session() as db_sess:
            for scope_id in [project_scope_id_1, project_scope_id_2]:
                db_sess.add(
                    AssociationScopesEntitiesRow(
                        scope_type=ScopeType.PROJECT,
                        scope_id=scope_id,
                        entity_type=EntityType.CONTAINER_REGISTRY,
                        entity_id=entity_id,
                    )
                )
            await db_sess.flush()

        binder = RBACScopeBinder(
            element_type=RBACElementType.CONTAINER_REGISTRY,
            entity_id=entity_id,
            unbind_scope_refs=[
                RBACElementRef(RBACElementType.PROJECT, project_scope_id_1),
                RBACElementRef(RBACElementType.PROJECT, project_scope_id_2),
            ],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert result.unbound_count == 2

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 0

    async def test_unbind_nonexistent_scope_returns_zero(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_scope_id_1: str,
    ) -> None:
        """Test unbinding a scope that was never bound returns zero count."""
        binder = RBACScopeBinder(
            element_type=RBACElementType.CONTAINER_REGISTRY,
            entity_id=entity_id,
            unbind_scope_refs=[
                RBACElementRef(RBACElementType.PROJECT, project_scope_id_1),
            ],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert result.unbound_count == 0

    async def test_unbind_preserves_other_entities_associations(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_scope_id_1: str,
    ) -> None:
        """Test that unbinding only affects the target entity's associations."""
        other_entity_id = str(uuid.uuid4())

        async with database_connection.begin_session() as db_sess:
            for eid in [entity_id, other_entity_id]:
                db_sess.add(
                    AssociationScopesEntitiesRow(
                        scope_type=ScopeType.PROJECT,
                        scope_id=project_scope_id_1,
                        entity_type=EntityType.CONTAINER_REGISTRY,
                        entity_id=eid,
                    )
                )
            await db_sess.flush()

        binder = RBACScopeBinder(
            element_type=RBACElementType.CONTAINER_REGISTRY,
            entity_id=entity_id,
            unbind_scope_refs=[
                RBACElementRef(RBACElementType.PROJECT, project_scope_id_1),
            ],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert result.unbound_count == 1

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 1

            remaining = await db_sess.scalar(sa.select(AssociationScopesEntitiesRow))
            assert remaining is not None
            assert remaining.entity_id == other_entity_id


# =============================================================================
# Mixed Bind/Unbind Tests
# =============================================================================


class TestRBACScopeBinderMixed:
    """Tests for simultaneous bind and unbind operations."""

    async def test_bind_and_unbind_in_single_operation(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_scope_id_1: str,
        project_scope_id_2: str,
        project_scope_id_3: str,
    ) -> None:
        """Test binding new scopes and unbinding old scopes atomically."""
        # Setup: entity is associated with project 1 and 2
        async with database_connection.begin_session() as db_sess:
            for scope_id in [project_scope_id_1, project_scope_id_2]:
                db_sess.add(
                    AssociationScopesEntitiesRow(
                        scope_type=ScopeType.PROJECT,
                        scope_id=scope_id,
                        entity_type=EntityType.CONTAINER_REGISTRY,
                        entity_id=entity_id,
                    )
                )
            await db_sess.flush()

        # Unbind project 1, bind project 3
        binder = RBACScopeBinder(
            element_type=RBACElementType.CONTAINER_REGISTRY,
            entity_id=entity_id,
            bind_scope_refs=[
                RBACElementRef(RBACElementType.PROJECT, project_scope_id_3),
            ],
            unbind_scope_refs=[
                RBACElementRef(RBACElementType.PROJECT, project_scope_id_1),
            ],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert result.bound_count == 1
            assert result.unbound_count == 1

            assoc_rows = (await db_sess.scalars(sa.select(AssociationScopesEntitiesRow))).all()
            assert len(assoc_rows) == 2

            scope_ids = {row.scope_id for row in assoc_rows}
            assert project_scope_id_2 in scope_ids
            assert project_scope_id_3 in scope_ids
            assert project_scope_id_1 not in scope_ids

    async def test_bind_and_unbind_with_mixed_scope_types(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_scope_id_1: str,
        domain_scope_id: str,
    ) -> None:
        """Test binding domain scope while unbinding project scope."""
        # Setup: entity associated with project
        async with database_connection.begin_session() as db_sess:
            db_sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.PROJECT,
                    scope_id=project_scope_id_1,
                    entity_type=EntityType.RESOURCE_GROUP,
                    entity_id=entity_id,
                )
            )
            await db_sess.flush()

        # Unbind project, bind domain
        binder = RBACScopeBinder(
            element_type=RBACElementType.RESOURCE_GROUP,
            entity_id=entity_id,
            bind_scope_refs=[
                RBACElementRef(RBACElementType.DOMAIN, domain_scope_id),
            ],
            unbind_scope_refs=[
                RBACElementRef(RBACElementType.PROJECT, project_scope_id_1),
            ],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert result.bound_count == 1
            assert result.unbound_count == 1

            assoc_row = await db_sess.scalar(sa.select(AssociationScopesEntitiesRow))
            assert assoc_row is not None
            assert assoc_row.scope_type == ScopeType.DOMAIN
            assert assoc_row.scope_id == domain_scope_id
            assert assoc_row.entity_type == EntityType.RESOURCE_GROUP

    async def test_both_empty_is_noop(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
    ) -> None:
        """Test that empty bind and unbind is a no-op."""
        binder = RBACScopeBinder(
            element_type=RBACElementType.CONTAINER_REGISTRY,
            entity_id=entity_id,
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert result.bound_count == 0
            assert result.unbound_count == 0
