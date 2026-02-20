"""
Tests for PermissionControllerRepository.search_element_associations() functionality.
Tests the repository layer with real database operations.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest

from ai.backend.manager.data.permission.types import EntityType, ScopeType
from ai.backend.manager.models.rbac_models import UserRoleRow
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.permission_controller.options import (
    EntityScopeConditions,
)
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.testutils.db import with_tables


@dataclass
class CreatedAssociation:
    id: uuid.UUID
    scope_type: ScopeType
    scope_id: str
    entity_type: EntityType
    entity_id: str
    registered_at: datetime


class TestSearchElementAssociations:
    """Tests for searching element associations."""

    @pytest.fixture
    async def db_with_rbac_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                RoleRow,
                UserRoleRow,
                PermissionRow,
                ObjectPermissionRow,
                AssociationScopesEntitiesRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def repository(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> PermissionControllerRepository:
        return PermissionControllerRepository(db_with_rbac_tables)

    @pytest.fixture
    async def created_associations(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> list[CreatedAssociation]:
        """Create multiple entity associations for testing."""
        created: list[CreatedAssociation] = []
        base_time = datetime(2026, 1, 1, tzinfo=UTC)

        async with db_with_rbac_tables.begin_session() as db_sess:
            for i, (scope_type, scope_id, entity_type, entity_id) in enumerate([
                (ScopeType.DOMAIN, "test-domain", EntityType.USER, str(uuid.uuid4())),
                (ScopeType.DOMAIN, "test-domain", EntityType.USER, str(uuid.uuid4())),
                (ScopeType.PROJECT, str(uuid.uuid4()), EntityType.VFOLDER, str(uuid.uuid4())),
                (ScopeType.DOMAIN, "test-domain", EntityType.IMAGE, str(uuid.uuid4())),
            ]):
                registered_at = base_time + timedelta(minutes=i)
                row = AssociationScopesEntitiesRow(
                    scope_type=scope_type,
                    scope_id=scope_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    registered_at=registered_at,
                )
                db_sess.add(row)
                await db_sess.flush()
                created.append(
                    CreatedAssociation(
                        id=row.id,
                        scope_type=scope_type,
                        scope_id=scope_id,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        registered_at=row.registered_at,
                    )
                )

        return created

    async def test_search_element_associations_items_have_correct_data(
        self,
        repository: PermissionControllerRepository,
        created_associations: list[CreatedAssociation],
    ) -> None:
        """Returned items should contain correct scope and entity data."""
        querier = BatchQuerier(
            conditions=[
                EntityScopeConditions.by_entity_type(EntityType.IMAGE),
            ],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await repository.search_element_associations(querier)

        assert result.total_count == 1
        item = result.items[0]
        expected = next(a for a in created_associations if a.entity_type == EntityType.IMAGE)
        assert item.object_id.entity_id == expected.entity_id
        assert item.scope_id.scope_type == expected.scope_type
        assert item.scope_id.scope_id == expected.scope_id
