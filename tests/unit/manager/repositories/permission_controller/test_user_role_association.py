"""
Tests for association_scopes_entities management on user_roles mutations.

Verifies that assign_role creates and revoke_role deletes the corresponding
AssociationScopesEntitiesRow so the role becomes visible to the user through RBAC.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.data.permission.role import (
    UserRoleAssignmentInput,
    UserRoleRevocationInput,
)
from ai.backend.manager.data.permission.types import EntityType, ScopeType
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.permission_controller.db_source.db_source import (
    PermissionDBSource,
)
from ai.backend.testutils.db import with_tables


class TestUserRoleAssociation:
    """Tests that user_roles mutations create/delete association_scopes_entities records."""

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
    def db_source(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> PermissionDBSource:
        return PermissionDBSource(db_with_rbac_tables)

    @pytest.fixture
    async def role_id(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
    ) -> uuid.UUID:
        role_id = uuid.uuid4()
        async with db_with_rbac_tables.begin_session() as db_sess:
            db_sess.add(RoleRow(id=role_id, name="test-role"))
            await db_sess.flush()
        return role_id

    async def _count_associations(
        self,
        db: ExtendedAsyncSAEngine,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
    ) -> int:
        async with db.begin_readonly_session_read_committed() as db_sess:
            result = await db_sess.scalar(
                sa.select(sa.func.count()).where(
                    sa.and_(
                        AssociationScopesEntitiesRow.scope_type
                        == RBACElementType.USER.to_scope_type(),
                        AssociationScopesEntitiesRow.scope_id == str(user_id),
                        AssociationScopesEntitiesRow.entity_type
                        == RBACElementType.ROLE.to_entity_type(),
                        AssociationScopesEntitiesRow.entity_id == str(role_id),
                    )
                )
            )
            return result or 0

    async def test_assign_role_creates_association(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        db_source: PermissionDBSource,
        role_id: uuid.UUID,
    ) -> None:
        """assign_role should create an association_scopes_entities record."""
        user_id = uuid.uuid4()

        assert await self._count_associations(db_with_rbac_tables, user_id, role_id) == 0

        await db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_id, role_id=role_id, granted_by=None)
        )

        assert await self._count_associations(db_with_rbac_tables, user_id, role_id) == 1

    async def test_revoke_role_deletes_association(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        db_source: PermissionDBSource,
        role_id: uuid.UUID,
    ) -> None:
        """revoke_role should delete the association_scopes_entities record."""
        user_id = uuid.uuid4()

        await db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_id, role_id=role_id, granted_by=None)
        )
        assert await self._count_associations(db_with_rbac_tables, user_id, role_id) == 1

        await db_source.revoke_role(UserRoleRevocationInput(user_id=user_id, role_id=role_id))

        assert await self._count_associations(db_with_rbac_tables, user_id, role_id) == 0

    async def test_assign_role_association_has_correct_types(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        db_source: PermissionDBSource,
        role_id: uuid.UUID,
    ) -> None:
        """The created association should have USER scope and ROLE entity types."""
        user_id = uuid.uuid4()

        await db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_id, role_id=role_id, granted_by=None)
        )

        async with db_with_rbac_tables.begin_readonly_session_read_committed() as db_sess:
            row = await db_sess.scalar(
                sa.select(AssociationScopesEntitiesRow).where(
                    sa.and_(
                        AssociationScopesEntitiesRow.scope_id == str(user_id),
                        AssociationScopesEntitiesRow.entity_id == str(role_id),
                    )
                )
            )
            assert row is not None
            assert row.scope_type == ScopeType.USER
            assert row.entity_type == EntityType.ROLE

    async def test_revoke_preserves_other_associations(
        self,
        db_with_rbac_tables: ExtendedAsyncSAEngine,
        db_source: PermissionDBSource,
        role_id: uuid.UUID,
    ) -> None:
        """Revoking one user's role should not affect another user's association."""
        user_id_1 = uuid.uuid4()
        user_id_2 = uuid.uuid4()

        await db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_id_1, role_id=role_id, granted_by=None)
        )
        await db_source.assign_role(
            UserRoleAssignmentInput(user_id=user_id_2, role_id=role_id, granted_by=None)
        )

        await db_source.revoke_role(UserRoleRevocationInput(user_id=user_id_1, role_id=role_id))

        assert await self._count_associations(db_with_rbac_tables, user_id_1, role_id) == 0
        assert await self._count_associations(db_with_rbac_tables, user_id_2, role_id) == 1
