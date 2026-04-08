"""
Tests for PermissionDBSource.search_roles_in_scope() functionality.
Tests the db_source layer with real database operations, verifying that
scoped role search correctly filters via association_scopes_entities.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.data.permission.types import EntityType, ScopeType
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base import BatchQuerier, OffsetPagination
from ai.backend.manager.repositories.permission_controller.db_source.db_source import (
    PermissionDBSource,
)
from ai.backend.manager.repositories.permission_controller.types import ScopedRoleSearchScope
from ai.backend.testutils.db import with_tables


@dataclass
class ScopedRoleFixture:
    project_id: uuid.UUID
    role_in_scope: uuid.UUID
    role_outside_scope: uuid.UUID


class TestSearchRolesInScope:
    """Tests for searching roles registered in a scope via association_scopes_entities."""

    @pytest.fixture
    async def db_with_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(
            database_connection,
            [
                RoleRow,
                AssociationScopesEntitiesRow,
            ],
        ):
            yield database_connection

    @pytest.fixture
    def db_source(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
    ) -> PermissionDBSource:
        return PermissionDBSource(db_with_tables)

    @pytest.fixture
    async def scoped_roles(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
    ) -> ScopedRoleFixture:
        """Create two roles: one registered in a project scope, one not."""
        project_id = uuid.uuid4()

        async with db_with_tables.begin_session() as db_sess:
            role_in = RoleRow(name="role-in-scope", description="In scope")
            role_out = RoleRow(name="role-outside-scope", description="Outside scope")
            db_sess.add(role_in)
            db_sess.add(role_out)
            await db_sess.flush()

            assoc = AssociationScopesEntitiesRow(
                scope_type=ScopeType.PROJECT,
                scope_id=str(project_id),
                entity_type=EntityType.ROLE,
                entity_id=str(role_in.id),
            )
            db_sess.add(assoc)
            await db_sess.flush()

        return ScopedRoleFixture(
            project_id=project_id,
            role_in_scope=role_in.id,
            role_outside_scope=role_out.id,
        )

    async def test_returns_only_roles_in_scope(
        self,
        db_source: PermissionDBSource,
        scoped_roles: ScopedRoleFixture,
    ) -> None:
        """Only roles registered in the given scope should be returned."""
        scope = ScopedRoleSearchScope(
            element_type=RBACElementType.PROJECT,
            scope_id=str(scoped_roles.project_id),
        )
        querier = BatchQuerier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await db_source.search_roles_in_scope(querier, scope)

        role_ids = [r.id for r in result.items]
        assert scoped_roles.role_in_scope in role_ids
        assert scoped_roles.role_outside_scope not in role_ids

    async def test_returns_correct_total_count(
        self,
        db_source: PermissionDBSource,
        scoped_roles: ScopedRoleFixture,
    ) -> None:
        """Total count should reflect only roles in scope."""
        scope = ScopedRoleSearchScope(
            element_type=RBACElementType.PROJECT,
            scope_id=str(scoped_roles.project_id),
        )
        querier = BatchQuerier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await db_source.search_roles_in_scope(querier, scope)

        assert result.total_count == 1

    async def test_empty_scope_returns_no_roles(
        self,
        db_source: PermissionDBSource,
        scoped_roles: ScopedRoleFixture,
    ) -> None:
        """A scope with no registered roles should return empty results."""
        empty_project_id = uuid.uuid4()
        scope = ScopedRoleSearchScope(
            element_type=RBACElementType.PROJECT,
            scope_id=str(empty_project_id),
        )
        querier = BatchQuerier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        result = await db_source.search_roles_in_scope(querier, scope)

        assert result.items == []
        assert result.total_count == 0

    async def test_different_scope_types_are_isolated(
        self,
        db_source: PermissionDBSource,
        db_with_tables: ExtendedAsyncSAEngine,
    ) -> None:
        """Roles in PROJECT scope should not appear when searching DOMAIN scope."""
        scope_id = str(uuid.uuid4())

        async with db_with_tables.begin_session() as db_sess:
            role = RoleRow(name="project-only-role")
            db_sess.add(role)
            await db_sess.flush()

            assoc = AssociationScopesEntitiesRow(
                scope_type=ScopeType.PROJECT,
                scope_id=scope_id,
                entity_type=EntityType.ROLE,
                entity_id=str(role.id),
            )
            db_sess.add(assoc)
            await db_sess.flush()

        querier = BatchQuerier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        # Search with DOMAIN scope using the same scope_id
        domain_scope = ScopedRoleSearchScope(
            element_type=RBACElementType.DOMAIN,
            scope_id=scope_id,
        )
        result = await db_source.search_roles_in_scope(querier, domain_scope)
        assert result.items == []

        # Search with PROJECT scope should find it
        project_scope = ScopedRoleSearchScope(
            element_type=RBACElementType.PROJECT,
            scope_id=scope_id,
        )
        result = await db_source.search_roles_in_scope(querier, project_scope)
        assert len(result.items) == 1
