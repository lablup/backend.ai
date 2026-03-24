"""
Regression test for BA-5277: RBAC cleanup on vfolder ownership transfer.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.types import EntityType, ScopeType
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.permission_controller.role_manager import RoleManager


class TestOwnershipTransferRBACCleanup:
    @pytest.fixture
    async def db(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        yield database_engine
        async with database_engine.begin_session() as sess:
            await sess.execute(sa.delete(AssociationScopesEntitiesRow))
            await sess.execute(sa.delete(UserRoleRow))
            await sess.execute(sa.delete(RoleRow))

    async def test_unmap_entity_from_scope_removes_association(
        self,
        db: ExtendedAsyncSAEngine,
    ) -> None:
        """
        After ownership transfer, the old owner's scope-entity mapping
        (AssociationScopesEntitiesRow) must be deleted so that re-invite
        does not hit IntegrityError → InFailedSQLTransactionError.
        """
        role_manager = RoleManager()
        user_id = uuid.uuid4()
        vfolder_id = uuid.uuid4()
        entity_id = ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(vfolder_id))
        scope_id = ScopeId(ScopeType.USER, str(user_id))

        # Simulate invitation-accept: create scope-entity mapping
        async with db.begin_session() as sess:
            await role_manager.map_entity_to_scope(sess, entity_id=entity_id, scope_id=scope_id)

        # Verify row exists
        async with db.begin_session() as sess:
            count = await sess.scalar(
                sa.select(sa.func.count()).where(
                    sa.and_(
                        AssociationScopesEntitiesRow.scope_id == str(user_id),
                        AssociationScopesEntitiesRow.entity_id == str(vfolder_id),
                    )
                )
            )
            assert count == 1

        # Simulate ownership transfer cleanup
        async with db.begin_session() as sess:
            await role_manager.unmap_entity_from_scope(sess, entity_id=entity_id, scope_id=scope_id)

        # Verify row removed
        async with db.begin_session() as sess:
            count = await sess.scalar(
                sa.select(sa.func.count()).where(
                    sa.and_(
                        AssociationScopesEntitiesRow.scope_id == str(user_id),
                        AssociationScopesEntitiesRow.entity_id == str(vfolder_id),
                    )
                )
            )
            assert count == 0, (
                "AssociationScopesEntitiesRow should be removed after unmap_entity_from_scope"
            )
