"""Integration tests for RBAC entity scope syncer with real database."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa

from ai.backend.common.data.permission.types import RelationType
from ai.backend.manager.data.permission.types import (
    EntityType,
    RBACElementRef,
    RBACElementType,
    ScopeType,
)
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.repositories.base.rbac.scope_syncer import (
    RBACEntityScopeSyncer,
    RBACEntityScopeSyncerResult,
    SyncAction,
    execute_rbac_entity_scope_syncer,
)
from ai.backend.testutils.db import with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def create_tables(
    database_connection: ExtendedAsyncSAEngine,
) -> AsyncGenerator[None, None]:
    async with with_tables(database_connection, [AssociationScopesEntitiesRow]):
        yield


@pytest.fixture
def entity_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def scope_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def scope_id_2() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def scope_id_3() -> str:
    return str(uuid.uuid4())


# =============================================================================
# Create Tests
# =============================================================================


class TestRBACEntityScopeSyncerCreate:
    """Tests for first-time scope association (CREATED action)."""

    async def test_creates_association(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        scope_id: str,
    ) -> None:
        """First sync creates an association and returns CREATED."""
        syncer = RBACEntityScopeSyncer(
            entity_ref=RBACElementRef(RBACElementType.VFOLDER, entity_id),
            desired_scope_ref=RBACElementRef(RBACElementType.USER, scope_id),
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_entity_scope_syncer(db_sess, syncer)

            assert isinstance(result, RBACEntityScopeSyncerResult)
            assert result.action is SyncAction.CREATED
            assert result.association_row is not None
            assert result.association_row.scope_type == ScopeType.USER
            assert result.association_row.scope_id == scope_id
            assert result.association_row.entity_type == EntityType.VFOLDER
            assert result.association_row.entity_id == entity_id
            assert result.unbound_rows == []


# =============================================================================
# Unchanged Tests
# =============================================================================


class TestRBACEntityScopeSyncerUnchanged:
    """Tests for idempotent re-sync (UNCHANGED action)."""

    async def test_same_scope_repeated(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        scope_id: str,
    ) -> None:
        """Re-syncing same scope returns UNCHANGED and no new rows."""
        syncer = RBACEntityScopeSyncer(
            entity_ref=RBACElementRef(RBACElementType.VFOLDER, entity_id),
            desired_scope_ref=RBACElementRef(RBACElementType.USER, scope_id),
        )

        async with database_connection.begin_session() as db_sess:
            result1 = await execute_rbac_entity_scope_syncer(db_sess, syncer)
            assert result1.action is SyncAction.CREATED

        async with database_connection.begin_session() as db_sess:
            result2 = await execute_rbac_entity_scope_syncer(db_sess, syncer)

            assert result2.action is SyncAction.UNCHANGED
            assert result2.association_row is None
            assert result2.unbound_rows == []

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 1


# =============================================================================
# Rebind Tests
# =============================================================================


class TestRBACEntityScopeSyncerRebind:
    """Tests for scope migration (REBOUND action)."""

    async def test_rebinds_to_new_scope(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        scope_id: str,
        scope_id_2: str,
    ) -> None:
        """Moving entity to new scope returns REBOUND, old removed, new created."""
        syncer_v1 = RBACEntityScopeSyncer(
            entity_ref=RBACElementRef(RBACElementType.VFOLDER, entity_id),
            desired_scope_ref=RBACElementRef(RBACElementType.USER, scope_id),
        )
        syncer_v2 = RBACEntityScopeSyncer(
            entity_ref=RBACElementRef(RBACElementType.VFOLDER, entity_id),
            desired_scope_ref=RBACElementRef(RBACElementType.USER, scope_id_2),
        )

        async with database_connection.begin_session() as db_sess:
            await execute_rbac_entity_scope_syncer(db_sess, syncer_v1)

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_entity_scope_syncer(db_sess, syncer_v2)

            assert result.action is SyncAction.REBOUND
            assert result.association_row is not None
            assert result.association_row.scope_id == scope_id_2
            assert len(result.unbound_rows) == 1
            assert result.unbound_rows[0].scope_id == scope_id

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 1

    async def test_cleans_up_multiple_stale_associations(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        scope_id: str,
        scope_id_2: str,
        scope_id_3: str,
    ) -> None:
        """Rebind removes all stale associations when multiple exist."""
        # Manually insert two associations with different scope_types
        # to simulate a state where multiple stale rows exist for the same scope_type.
        async with database_connection.begin_session() as db_sess:
            db_sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.USER,
                    scope_id=scope_id,
                    entity_type=EntityType.VFOLDER,
                    entity_id=entity_id,
                    relation_type=RelationType.AUTO,
                ),
            )
            db_sess.add(
                AssociationScopesEntitiesRow(
                    scope_type=ScopeType.USER,
                    scope_id=scope_id_2,
                    entity_type=EntityType.VFOLDER,
                    entity_id=entity_id,
                    relation_type=RelationType.AUTO,
                ),
            )

        syncer = RBACEntityScopeSyncer(
            entity_ref=RBACElementRef(RBACElementType.VFOLDER, entity_id),
            desired_scope_ref=RBACElementRef(RBACElementType.USER, scope_id_3),
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_entity_scope_syncer(db_sess, syncer)

            assert result.action is SyncAction.REBOUND
            assert len(result.unbound_rows) == 2
            assert result.association_row is not None
            assert result.association_row.scope_id == scope_id_3

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 1


# =============================================================================
# Isolation Tests
# =============================================================================


class TestRBACEntityScopeSyncerIsolation:
    """Tests that syncer only affects the targeted entity/scope_type."""

    async def test_different_entity_unaffected(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        scope_id: str,
        scope_id_2: str,
    ) -> None:
        """Syncing one entity does not remove another entity's association."""
        entity_a = str(uuid.uuid4())
        entity_b = str(uuid.uuid4())

        syncer_a = RBACEntityScopeSyncer(
            entity_ref=RBACElementRef(RBACElementType.VFOLDER, entity_a),
            desired_scope_ref=RBACElementRef(RBACElementType.USER, scope_id),
        )
        syncer_b = RBACEntityScopeSyncer(
            entity_ref=RBACElementRef(RBACElementType.VFOLDER, entity_b),
            desired_scope_ref=RBACElementRef(RBACElementType.USER, scope_id_2),
        )

        async with database_connection.begin_session() as db_sess:
            await execute_rbac_entity_scope_syncer(db_sess, syncer_a)
            await execute_rbac_entity_scope_syncer(db_sess, syncer_b)

        # Re-sync entity_a to a new scope — entity_b should be unaffected
        syncer_a_v2 = RBACEntityScopeSyncer(
            entity_ref=RBACElementRef(RBACElementType.VFOLDER, entity_a),
            desired_scope_ref=RBACElementRef(RBACElementType.USER, scope_id_2),
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_entity_scope_syncer(db_sess, syncer_a_v2)
            assert result.action is SyncAction.REBOUND

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 2

    async def test_different_scope_type_unaffected(
        self,
        database_connection: ExtendedAsyncSAEngine,
        create_tables: None,
        entity_id: str,
        scope_id: str,
        scope_id_2: str,
    ) -> None:
        """Syncing within USER scope_type does not affect PROJECT scope_type."""
        # Create an association in USER scope
        syncer_user = RBACEntityScopeSyncer(
            entity_ref=RBACElementRef(RBACElementType.VFOLDER, entity_id),
            desired_scope_ref=RBACElementRef(RBACElementType.USER, scope_id),
        )
        # Create an association in PROJECT scope
        syncer_project = RBACEntityScopeSyncer(
            entity_ref=RBACElementRef(RBACElementType.VFOLDER, entity_id),
            desired_scope_ref=RBACElementRef(RBACElementType.PROJECT, scope_id_2),
        )

        async with database_connection.begin_session() as db_sess:
            await execute_rbac_entity_scope_syncer(db_sess, syncer_user)
            await execute_rbac_entity_scope_syncer(db_sess, syncer_project)

        # Re-sync USER scope to a different scope_id — PROJECT should be unaffected
        new_user_scope_id = str(uuid.uuid4())
        syncer_user_v2 = RBACEntityScopeSyncer(
            entity_ref=RBACElementRef(RBACElementType.VFOLDER, entity_id),
            desired_scope_ref=RBACElementRef(RBACElementType.USER, new_user_scope_id),
        )

        async with database_connection.begin_session() as db_sess:
            result = await execute_rbac_entity_scope_syncer(db_sess, syncer_user_v2)
            assert result.action is SyncAction.REBOUND

            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 2

            project_assoc = await db_sess.scalar(
                sa.select(AssociationScopesEntitiesRow).where(
                    AssociationScopesEntitiesRow.scope_type == ScopeType.PROJECT,
                )
            )
            assert project_assoc is not None
            assert project_assoc.scope_id == scope_id_2
