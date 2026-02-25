"""Integration tests for RBAC scope binder/unbinder with real database."""

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
    RBACScopeUnbinder,
    RBACScopeUnbinderResult,
    execute_rbac_scope_binder,
    execute_rbac_scope_unbinder,
)
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


# =============================================================================
# Tables & Fixtures
# =============================================================================

SCOPE_BINDER_TABLES = [
    AssociationScopesEntitiesRow,
]


@pytest.fixture
async def create_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    async with with_tables(database_connection, SCOPE_BINDER_TABLES):
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
# Binder Tests
# =============================================================================


class TestRBACScopeBinder:
    async def test_bind_single_scope(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_id_1: str,
    ) -> None:
        binder = RBACScopeBinder(
            element_type=RBACElementType.CONTAINER_REGISTRY,
            entity_id=entity_id,
            scope_refs=[RBACElementRef(RBACElementType.PROJECT, project_id_1)],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert isinstance(result, RBACScopeBinderResult)
            assert len(result.rows) == 1
            row = result.rows[0]
            assert row.scope_type == ScopeType.PROJECT
            assert row.scope_id == project_id_1
            assert row.entity_type == EntityType.CONTAINER_REGISTRY
            assert row.entity_id == entity_id
            assert row.relation_type == RelationType.AUTO

    async def test_bind_multiple_scopes(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_id_1: str,
        project_id_2: str,
        project_id_3: str,
    ) -> None:
        binder = RBACScopeBinder(
            element_type=RBACElementType.CONTAINER_REGISTRY,
            entity_id=entity_id,
            scope_refs=[
                RBACElementRef(RBACElementType.PROJECT, project_id_1),
                RBACElementRef(RBACElementType.PROJECT, project_id_2),
                RBACElementRef(RBACElementType.PROJECT, project_id_3),
            ],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert len(result.rows) == 3
            returned_scope_ids = {row.scope_id for row in result.rows}
            assert returned_scope_ids == {project_id_1, project_id_2, project_id_3}

    async def test_bind_duplicate_returns_empty(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_id_1: str,
    ) -> None:
        """Binding an already-bound scope returns no rows (ON CONFLICT DO NOTHING)."""
        binder = RBACScopeBinder(
            element_type=RBACElementType.CONTAINER_REGISTRY,
            entity_id=entity_id,
            scope_refs=[RBACElementRef(RBACElementType.PROJECT, project_id_1)],
        )

        async with database_connection.begin_session() as db_sess:
            first = await execute_rbac_scope_binder(db_sess, binder)
            assert len(first.rows) == 1

        async with database_connection.begin_session() as db_sess:
            second = await execute_rbac_scope_binder(db_sess, binder)
            assert len(second.rows) == 0

            total = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert total == 1

    async def test_bind_with_ref_relation_type(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_id_1: str,
    ) -> None:
        binder = RBACScopeBinder(
            element_type=RBACElementType.CONTAINER_REGISTRY,
            entity_id=entity_id,
            scope_refs=[RBACElementRef(RBACElementType.PROJECT, project_id_1)],
            relation_type=RelationType.REF,
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert len(result.rows) == 1
            assert result.rows[0].relation_type == RelationType.REF

    async def test_bind_empty_scope_refs(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
    ) -> None:
        binder = RBACScopeBinder(
            element_type=RBACElementType.CONTAINER_REGISTRY,
            entity_id=entity_id,
            scope_refs=[],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_binder(db_sess, binder)

            assert result.rows == []


# =============================================================================
# Unbinder Tests
# =============================================================================


class TestRBACScopeUnbinder:
    @pytest.fixture
    async def two_project_associations(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_id_1: str,
        project_id_2: str,
    ) -> None:
        """Seed two project scope associations for entity_id."""
        async with database_connection.begin_session() as db_sess:
            for pid in [project_id_1, project_id_2]:
                db_sess.add(
                    AssociationScopesEntitiesRow(
                        scope_type=ScopeType.PROJECT,
                        scope_id=pid,
                        entity_type=EntityType.CONTAINER_REGISTRY,
                        entity_id=entity_id,
                    )
                )
            await db_sess.flush()

    async def test_unbind_single_scope(
        self,
        database_connection: ExtendedAsyncSAEngine,
        two_project_associations: None,
        entity_id: str,
        project_id_1: str,
        project_id_2: str,
    ) -> None:
        unbinder = RBACScopeUnbinder(
            element_type=RBACElementType.CONTAINER_REGISTRY,
            entity_id=entity_id,
            scope_refs=[RBACElementRef(RBACElementType.PROJECT, project_id_1)],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_unbinder(db_sess, unbinder)

            assert isinstance(result, RBACScopeUnbinderResult)
            assert len(result.rows) == 1
            assert result.rows[0].scope_id == project_id_1

            remaining = await db_sess.scalar(sa.select(AssociationScopesEntitiesRow))
            assert remaining is not None
            assert remaining.scope_id == project_id_2

    async def test_unbind_all_scopes(
        self,
        database_connection: ExtendedAsyncSAEngine,
        two_project_associations: None,
        entity_id: str,
        project_id_1: str,
        project_id_2: str,
    ) -> None:
        unbinder = RBACScopeUnbinder(
            element_type=RBACElementType.CONTAINER_REGISTRY,
            entity_id=entity_id,
            scope_refs=[
                RBACElementRef(RBACElementType.PROJECT, project_id_1),
                RBACElementRef(RBACElementType.PROJECT, project_id_2),
            ],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_unbinder(db_sess, unbinder)

            assert len(result.rows) == 2
            total = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert total == 0

    async def test_unbind_nonexistent_returns_empty(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_id_1: str,
    ) -> None:
        unbinder = RBACScopeUnbinder(
            element_type=RBACElementType.CONTAINER_REGISTRY,
            entity_id=entity_id,
            scope_refs=[RBACElementRef(RBACElementType.PROJECT, project_id_1)],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_unbinder(db_sess, unbinder)
            assert result.rows == []

    async def test_unbind_preserves_other_entities(
        self,
        database_connection: ExtendedAsyncSAEngine,
        two_project_associations: None,
        entity_id: str,
        project_id_1: str,
    ) -> None:
        """Unbinding only affects the target entity, not other entities on the same scope."""
        other_entity_id = str(uuid.uuid4())

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
            element_type=RBACElementType.CONTAINER_REGISTRY,
            entity_id=entity_id,
            scope_refs=[RBACElementRef(RBACElementType.PROJECT, project_id_1)],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_unbinder(db_sess, unbinder)

            assert len(result.rows) == 1
            assert result.rows[0].entity_id == entity_id

            remaining = (await db_sess.scalars(sa.select(AssociationScopesEntitiesRow))).all()
            remaining_entity_ids = {r.entity_id for r in remaining}
            assert entity_id not in remaining_entity_ids or all(
                r.scope_id != project_id_1 for r in remaining if r.entity_id == entity_id
            )
            assert other_entity_id in remaining_entity_ids

    async def test_unbind_empty_scope_refs(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
    ) -> None:
        unbinder = RBACScopeUnbinder(
            element_type=RBACElementType.CONTAINER_REGISTRY,
            entity_id=entity_id,
            scope_refs=[],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_unbinder(db_sess, unbinder)
            assert result.rows == []

    async def test_unbind_with_mixed_scope_types(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        project_id_1: str,
        domain_id: str,
    ) -> None:
        """Unbind can target different scope types in one call."""
        async with database_connection.begin_session() as db_sess:
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

        unbinder = RBACScopeUnbinder(
            element_type=RBACElementType.RESOURCE_GROUP,
            entity_id=entity_id,
            scope_refs=[
                RBACElementRef(RBACElementType.PROJECT, project_id_1),
                RBACElementRef(RBACElementType.DOMAIN, domain_id),
            ],
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_scope_unbinder(db_sess, unbinder)

            assert len(result.rows) == 2
            returned_scope_types = {row.scope_type for row in result.rows}
            assert ScopeType.PROJECT in returned_scope_types
            assert ScopeType.DOMAIN in returned_scope_types
