"""
Tests for PermissionControllerRepository.create_role() with scope_refs.
Verifies that role creation with scope associations correctly inserts
both the role row and association_scopes_entities rows.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Sequence
from typing import TYPE_CHECKING

import pytest
import sqlalchemy as sa

from ai.backend.common.data.permission.types import (
    EntityType,
    RBACElementType,
    RelationType,
    RoleSource,
    ScopeType,
)
from ai.backend.manager.data.permission.status import RoleStatus
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.permission_controller.creators import RoleCreatorSpec
from ai.backend.manager.repositories.permission_controller.db_source.db_source import (
    CreateRoleInput,
)
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.testutils.db import TableOrORM, with_tables

if TYPE_CHECKING:
    from ai.backend.manager.models.utils import ExtendedAsyncSAEngine


CREATE_ROLE_TABLES: Sequence[TableOrORM] = [
    RoleRow,
    AssociationScopesEntitiesRow,
]


class TestCreateRoleWithScopeRefs:
    """Tests for creating roles with scope associations."""

    @pytest.fixture
    async def db_with_tables(
        self,
        database_connection: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        async with with_tables(database_connection, CREATE_ROLE_TABLES):
            yield database_connection

    @pytest.fixture
    def repository(
        self,
        db_with_tables: ExtendedAsyncSAEngine,
    ) -> PermissionControllerRepository:
        return PermissionControllerRepository(db_with_tables)

    def _make_role_creator_spec(
        self,
        name: str = "test-role",
        source: RoleSource = RoleSource.CUSTOM,
        status: RoleStatus = RoleStatus.ACTIVE,
    ) -> RoleCreatorSpec:
        return RoleCreatorSpec(
            name=name,
            source=source,
            status=status,
        )

    async def test_create_role_with_single_scope_ref(
        self,
        repository: PermissionControllerRepository,
        db_with_tables: ExtendedAsyncSAEngine,
    ) -> None:
        """Role creation with a single scope_ref should insert one association row."""
        domain_id = str(uuid.uuid4())
        scope_ref = RBACElementRef(
            element_type=RBACElementType.DOMAIN,
            element_id=domain_id,
        )
        spec = self._make_role_creator_spec(name="domain-admin")
        input_data = CreateRoleInput(
            creator=Creator(spec=spec),
            object_permissions=[],
            scope_refs=[scope_ref],
        )

        role_data = await repository.create_role(input_data)

        assert role_data.name == "domain-admin"

        async with db_with_tables.begin_session() as db_sess:
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 1

            assoc_row = await db_sess.scalar(sa.select(AssociationScopesEntitiesRow))
            assert assoc_row is not None
            assert assoc_row.scope_type == ScopeType.DOMAIN
            assert assoc_row.scope_id == domain_id
            assert assoc_row.entity_type == EntityType.ROLE
            assert assoc_row.entity_id == str(role_data.id)
            assert assoc_row.relation_type == RelationType.AUTO

    async def test_create_role_with_multiple_scope_refs(
        self,
        repository: PermissionControllerRepository,
        db_with_tables: ExtendedAsyncSAEngine,
    ) -> None:
        """Role creation with multiple scope_refs should insert one association per scope."""
        domain_id = str(uuid.uuid4())
        project_id = str(uuid.uuid4())
        scope_refs = [
            RBACElementRef(element_type=RBACElementType.DOMAIN, element_id=domain_id),
            RBACElementRef(element_type=RBACElementType.PROJECT, element_id=project_id),
        ]
        spec = self._make_role_creator_spec(name="multi-scope-role")
        input_data = CreateRoleInput(
            creator=Creator(spec=spec),
            object_permissions=[],
            scope_refs=scope_refs,
        )

        role_data = await repository.create_role(input_data)

        assert role_data.name == "multi-scope-role"

        async with db_with_tables.begin_session() as db_sess:
            assoc_rows = list(
                await db_sess.scalars(
                    sa.select(AssociationScopesEntitiesRow).where(
                        AssociationScopesEntitiesRow.entity_id == str(role_data.id),
                    )
                )
            )
            assert len(assoc_rows) == 2

            scope_types = {row.scope_type for row in assoc_rows}
            assert ScopeType.DOMAIN in scope_types
            assert ScopeType.PROJECT in scope_types

            scope_ids = {row.scope_id for row in assoc_rows}
            assert domain_id in scope_ids
            assert project_id in scope_ids

            for row in assoc_rows:
                assert row.entity_type == EntityType.ROLE
                assert row.relation_type == RelationType.AUTO

    async def test_create_role_without_scope_refs(
        self,
        repository: PermissionControllerRepository,
        db_with_tables: ExtendedAsyncSAEngine,
    ) -> None:
        """Role creation without scope_refs should not insert any association rows."""
        spec = self._make_role_creator_spec(name="unscoped-role")
        input_data = CreateRoleInput(
            creator=Creator(spec=spec),
            object_permissions=[],
            scope_refs=[],
        )

        role_data = await repository.create_role(input_data)

        assert role_data.name == "unscoped-role"

        async with db_with_tables.begin_session() as db_sess:
            assoc_count = await db_sess.scalar(
                sa.select(sa.func.count()).select_from(AssociationScopesEntitiesRow)
            )
            assert assoc_count == 0
