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
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession as SASession

from ai.backend.common.data.entity.domain import DomainID
from ai.backend.common.data.entity.project import ProjectEntityType, ProjectID
from ai.backend.common.data.entity.role import RoleEntityType
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


async def _add_role(
    db_sess: SASession, name: str, scope_type: EntityType, scope_id: uuid.UUID
) -> uuid.UUID:
    """A role of the scope: on the row, and under the scope in the graph as
    ``_created_in`` does. The scope's node is created if it has none."""
    scope_node = await db_sess.scalar(
        sa.select(VirtualEntityRow).where(
            VirtualEntityRow.entity_type == scope_type, VirtualEntityRow.entity_id == scope_id
        )
    )
    if scope_node is None:
        scope_node = VirtualEntityRow(entity_type=scope_type, entity_id=scope_id)
        db_sess.add(scope_node)
        await db_sess.flush()
        db_sess.add(
            EntityMembershipRow(virtual_entity_id=scope_node.id, member_entity_id=scope_node.id)
        )
    role = RoleRow(name=name, description=name, scope_type=scope_type, scope_id=scope_id)
    db_sess.add(role)
    await db_sess.flush()
    role_node = VirtualEntityRow(entity_type=RoleEntityType(), entity_id=role.id)
    db_sess.add(role_node)
    await db_sess.flush()
    db_sess.add(EntityMembershipRow(virtual_entity_id=role_node.id, member_entity_id=role_node.id))
    db_sess.add(EntityMembershipRow(virtual_entity_id=scope_node.id, member_entity_id=role_node.id))
    await db_sess.flush()
    return role.id


class TestSearchRolesInScope:
    """Tests for searching the roles of a scope."""

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
        """Create two roles: one of the project, one of another project."""
        project_id = uuid.uuid4()

        async with db_with_tables.begin_session() as db_sess:
            role_in = await _add_role(db_sess, "role-in-scope", ProjectEntityType(), project_id)
            role_out = await _add_role(
                db_sess, "role-outside-scope", ProjectEntityType(), uuid.uuid4()
            )

        return ScopedRoleFixture(
            project_id=project_id,
            role_in_scope=role_in,
            role_outside_scope=role_out,
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
            await _add_role(db_sess, "project-only-role", ProjectEntityType(), scope_id)

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
