"""
Regression test for BA-5277: RBAC cleanup on vfolder ownership transfer.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import sqlalchemy as sa

from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    RoleSource,
    ScopeType,
)
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission_group import PermissionGroupRow
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
            await sess.execute(sa.delete(ObjectPermissionRow))
            await sess.execute(sa.delete(PermissionGroupRow))
            await sess.execute(sa.delete(AssociationScopesEntitiesRow))
            await sess.execute(sa.delete(UserRoleRow))
            await sess.execute(sa.delete(RoleRow))

    async def _setup_user_rbac(
        self,
        db: ExtendedAsyncSAEngine,
        user_id: uuid.UUID,
    ) -> None:
        """Create RoleRow → UserRoleRow → PermissionGroupRow for a user."""
        async with db.begin_session() as sess:
            role = RoleRow(name=f"role-{user_id.hex[:8]}", source=RoleSource.SYSTEM)
            sess.add(role)
            await sess.flush()
            sess.add(UserRoleRow(user_id=user_id, role_id=role.id))
            sess.add(
                PermissionGroupRow(
                    role_id=role.id,
                    scope_type=ScopeType.USER,
                    scope_id=str(user_id),
                )
            )
            await sess.flush()

    async def _simulate_invite_accept(
        self,
        db: ExtendedAsyncSAEngine,
        role_manager: RoleManager,
        user_id: uuid.UUID,
        vfolder_entity_id: ObjectId,
    ) -> None:
        """Reproduce what create_vfolder_permission does for RBAC."""
        scope_id = ScopeId(ScopeType.USER, str(user_id))
        async with db.begin_session() as sess:
            await role_manager.map_entity_to_scope(
                sess,
                entity_id=vfolder_entity_id,
                scope_id=scope_id,
            )
            await role_manager.add_object_permission_to_user_role(
                sess,
                user_id=user_id,
                entity_id=vfolder_entity_id,
                operations=[OperationType.READ],
            )

    async def _simulate_transfer_cleanup(
        self,
        db: ExtendedAsyncSAEngine,
        role_manager: RoleManager,
        old_owner_id: uuid.UUID,
        vfolder_entity_id: ObjectId,
        vfolder_id: uuid.UUID,
    ) -> None:
        """Reproduce the old-owner RBAC cleanup in change_vfolder_ownership."""
        async with db.begin_session() as sess:
            await role_manager.unmap_entity_from_scope(
                sess,
                entity_id=vfolder_entity_id,
                scope_id=ScopeId(ScopeType.USER, str(old_owner_id)),
            )
            try:
                await role_manager.delete_object_permission_of_user(
                    sess,
                    old_owner_id,
                    vfolder_id,
                )
            except (AttributeError, ValueError):
                pass

    async def _count_scope_entity(
        self,
        db: ExtendedAsyncSAEngine,
        user_id: uuid.UUID,
        vfolder_id: uuid.UUID,
    ) -> int:
        async with db.begin_session() as sess:
            return (
                await sess.scalar(
                    sa.select(sa.func.count()).where(
                        sa.and_(
                            AssociationScopesEntitiesRow.scope_id == str(user_id),
                            AssociationScopesEntitiesRow.entity_id == str(vfolder_id),
                        )
                    )
                )
                or 0
            )

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

        async with db.begin_session() as sess:
            await role_manager.map_entity_to_scope(sess, entity_id=entity_id, scope_id=scope_id)

        assert await self._count_scope_entity(db, user_id, vfolder_id) == 1

        async with db.begin_session() as sess:
            await role_manager.unmap_entity_from_scope(sess, entity_id=entity_id, scope_id=scope_id)

        assert await self._count_scope_entity(db, user_id, vfolder_id) == 0

    async def test_round_trip_transfer_then_reinvite(
        self,
        db: ExtendedAsyncSAEngine,
    ) -> None:
        """
        Regression test for BA-5277 (A→B→A round-trip):
        1. A owns vfolder, B accepts invitation (B gets RBAC records)
        2. Transfer A→B  — old owner A's RBAC cleaned up
        3. Transfer B→A  — old owner B's RBAC cleaned up (including invitee records from step 1)
        4. Re-invite B   — must succeed without unique constraint violation
        """
        role_manager = RoleManager()
        user_a = uuid.uuid4()
        user_b = uuid.uuid4()
        vfolder_id = uuid.uuid4()
        vfolder_entity_id = ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(vfolder_id))

        await self._setup_user_rbac(db, user_a)
        await self._setup_user_rbac(db, user_b)

        # Step 1: A owns vfolder, B accepts invitation
        await self._simulate_invite_accept(db, role_manager, user_b, vfolder_entity_id)
        assert await self._count_scope_entity(db, user_b, vfolder_id) == 1

        # Step 2: Transfer A→B — clean up old owner A
        await self._simulate_transfer_cleanup(
            db,
            role_manager,
            user_a,
            vfolder_entity_id,
            vfolder_id,
        )

        # Step 3: Transfer B→A — clean up old owner B
        await self._simulate_transfer_cleanup(
            db,
            role_manager,
            user_b,
            vfolder_entity_id,
            vfolder_id,
        )
        assert await self._count_scope_entity(db, user_b, vfolder_id) == 0

        # Step 4: Re-invite B — must not raise IntegrityError
        await self._simulate_invite_accept(db, role_manager, user_b, vfolder_entity_id)
        assert await self._count_scope_entity(db, user_b, vfolder_id) == 1
