"""
Tests for PermissionDBSource.search_roles_in_scope() functionality.
Tests the db_source layer with real database operations, verifying that
scoped role search correctly filters along scope -> virtual entity -> entity.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import pytest
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE, ProjectID
from ai.backend.common.data.entity.role import ROLE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.models.agent import AgentRow

# ORM cluster registration: configure_mappers() (triggered when this isolated
# test registers a domain-cluster row) resolves string relationships against the
# registry. These rows are reachable via relationships but are not otherwise
# imported/registered by this test; _ORM_CLUSTER keeps them live.
from ai.backend.manager.models.image import ImageRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.role.scopes import ScopedRoleOperationScope
from ai.backend.manager.models.resource_group import ResourceGroupForDomainRow
from ai.backend.manager.models.specs.pagination import OffsetPagination
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.models.virtual_entity.entity_membership import EntityMembershipRow
from ai.backend.manager.models.virtual_entity.virtual_entity import VirtualEntityRow
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.permission_controller.db_source.db_source import (
    PermissionDBSource,
)
from ai.backend.testutils.db import with_tables

_ORM_CLUSTER = (
    AgentRow,
    ImageRow,
    ResourceGroupForDomainRow,
)


@dataclass
class ScopedRoleFixture:
    project_id: uuid.UUID
    role_in_scope: uuid.UUID
    role_outside_scope: uuid.UUID


async def _own_role(
    db_sess: SASession, scope_type: EntityType, scope_id: uuid.UUID, role_id: uuid.UUID
) -> None:
    """Put the role under the scope in the graph, as ``_created_in`` does."""
    scope_node = VirtualEntityRow(entity_type=scope_type, entity_id=scope_id)
    role_node = VirtualEntityRow(entity_type=ROLE_ENTITY_TYPE, entity_id=role_id)
    db_sess.add_all([scope_node, role_node])
    await db_sess.flush()
    db_sess.add_all([
        EntityMembershipRow(virtual_entity_id=node.id, member_entity_id=node.id)
        for node in (scope_node, role_node)
    ])
    db_sess.add(EntityMembershipRow(virtual_entity_id=scope_node.id, member_entity_id=role_node.id))
    await db_sess.flush()


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
                VirtualEntityRow,
                EntityMembershipRow,
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
        """Create two roles: one owned by a project scope, one not."""
        project_id = uuid.uuid4()

        async with db_with_tables.begin_session() as db_sess:
            role_in = RoleRow(name="role-in-scope", description="In scope")
            role_out = RoleRow(name="role-outside-scope", description="Outside scope")
            db_sess.add(role_in)
            db_sess.add(role_out)
            await db_sess.flush()
            await _own_role(db_sess, PROJECT_ENTITY_TYPE, project_id, role_in.id)

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
        scope = ScopedRoleOperationScope(scope=ProjectID(scoped_roles.project_id))
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
        scope = ScopedRoleOperationScope(scope=ProjectID(scoped_roles.project_id))
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
        scope = ScopedRoleOperationScope(scope=ProjectID(empty_project_id))
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
        scope_id = uuid.uuid4()

        async with db_with_tables.begin_session() as db_sess:
            role = RoleRow(name="project-only-role")
            db_sess.add(role)
            await db_sess.flush()
            await _own_role(db_sess, PROJECT_ENTITY_TYPE, scope_id, role.id)

        querier = BatchQuerier(
            conditions=[],
            orders=[],
            pagination=OffsetPagination(limit=10, offset=0),
        )

        # Search with DOMAIN scope using the same scope_id
        domain_scope = ScopedRoleOperationScope(scope=DomainID(scope_id))
        result = await db_source.search_roles_in_scope(querier, domain_scope)
        assert result.items == []

        # Search with PROJECT scope should find it
        project_scope = ScopedRoleOperationScope(scope=ProjectID(scope_id))
        result = await db_source.search_roles_in_scope(querier, project_scope)
        assert len(result.items) == 1
