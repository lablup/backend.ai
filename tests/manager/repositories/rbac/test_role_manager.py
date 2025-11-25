"""Tests for RoleManager functionality."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Iterable, Mapping
from dataclasses import dataclass

import pytest
import sqlalchemy as sa

from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.types import (
    EntityType,
    OperationType,
    ScopeType,
)
from ai.backend.manager.errors.rbac import UserSystemRoleNotFound
from ai.backend.manager.models.rbac_models.association_scopes_entities import (
    AssociationScopesEntitiesRow,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.rbac_models.permission.permission_group import PermissionGroupRow
from ai.backend.manager.models.rbac_models.role import RoleRow
from ai.backend.manager.models.rbac_models.user_role import UserRoleRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.permission_controller.role_manager import (
    RoleManager,
)


@dataclass
class TestScopeSystemRoleData:
    """Test implementation of ScopeSystemRoleData protocol."""

    _scope_id: ScopeId
    _role_name: str
    _entity_operations: Mapping[EntityType, Iterable[OperationType]]

    def scope_id(self) -> ScopeId:
        return self._scope_id

    def role_name(self) -> str:
        return self._role_name

    def entity_operations(self) -> Mapping[EntityType, Iterable[OperationType]]:
        return self._entity_operations


class TestRoleManager:
    """Test cases for RoleManager with real database."""

    @pytest.fixture
    async def db_with_cleanup(
        self,
        database_engine: ExtendedAsyncSAEngine,
    ) -> AsyncGenerator[ExtendedAsyncSAEngine, None]:
        """Database engine that auto-cleans rbac data after each test"""
        yield database_engine

        async with database_engine.begin_session() as db_sess:
            await db_sess.execute(sa.delete(ObjectPermissionRow))
            await db_sess.execute(sa.delete(PermissionRow))
            await db_sess.execute(sa.delete(PermissionGroupRow))
            await db_sess.execute(sa.delete(UserRoleRow))
            await db_sess.execute(sa.delete(RoleRow))
            await db_sess.execute(sa.delete(AssociationScopesEntitiesRow))

    @pytest.fixture
    def role_manager(self) -> RoleManager:
        """Create a RoleManager instance."""
        return RoleManager()

    @pytest.fixture
    def test_user_id(self) -> uuid.UUID:
        """Create a test user ID."""
        return uuid.uuid4()

    @pytest.fixture
    def test_entity_id(self) -> ObjectId:
        """Create a test entity ID."""
        return ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(uuid.uuid4()))

    @pytest.fixture
    async def test_user_and_system_role_id(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        role_manager: RoleManager,
        test_user_id: uuid.UUID,
    ) -> AsyncGenerator[tuple[uuid.UUID, uuid.UUID], None]:
        """Create a system role and map it to a user. Returns role_id."""
        user_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=str(test_user_id))
        async with db_with_cleanup.begin_session() as db_sess:
            role_data = TestScopeSystemRoleData(
                _scope_id=user_scope_id,
                _role_name="user-system-role",
                _entity_operations={EntityType.VFOLDER: [OperationType.READ]},
            )
            role = await role_manager.create_system_role(db_sess, role_data)
            await role_manager.map_user_to_role(db_sess, test_user_id, role.id)
            role_id = role.id

        yield test_user_id, role_id

    @pytest.fixture
    async def test_entity_with_scope(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        role_manager: RoleManager,
        test_entity_id: ObjectId,
    ) -> AsyncGenerator[tuple[ObjectId, ScopeId], None]:
        """Create an entity and map it to a scope. Returns (entity_id, scope_id)."""
        entity_scope_id = ScopeId(scope_type=ScopeType.PROJECT, scope_id=str(uuid.uuid4()))

        async with db_with_cleanup.begin_session() as db_sess:
            await role_manager.map_entity_to_scope(db_sess, test_entity_id, entity_scope_id)

        yield (test_entity_id, entity_scope_id)

    @pytest.mark.asyncio
    async def test_add_object_permission_to_user_role(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        role_manager: RoleManager,
        test_user_and_system_role_id: tuple[uuid.UUID, uuid.UUID],
        test_entity_with_scope: tuple[ObjectId, ScopeId],
    ) -> None:
        """Test adding object permissions to a user's system role."""
        # Given: System role with user (from fixture)
        user_id, role_id = test_user_and_system_role_id

        # Given: Entity with scope (from fixture)
        entity_id, _ = test_entity_with_scope

        # When: Add object permissions
        operations = {OperationType.READ, OperationType.UPDATE}
        async with db_with_cleanup.begin_session() as db_sess:
            result = await role_manager.add_object_permission_to_user_role(
                db_sess, user_id, entity_id, operations
            )

        # Then: Verify permissions are added
        assert result.id == role_id
        added_permissions = {p.operation for p in result.object_permissions}
        assert added_permissions == operations
        assert len(result.permission_groups) == 2  # User scope + Entity scope
        assert len(result.object_permissions) == 2  # 2 operations

    @pytest.mark.asyncio
    async def test_add_object_permission_without_system_role(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        role_manager: RoleManager,
        test_user_id: uuid.UUID,
        test_entity_with_scope: tuple[ObjectId, ScopeId],
    ) -> None:
        test_entity_id, _ = test_entity_with_scope

        """Test that adding object permissions without a system role raises an error."""
        # When/Then: Try to add object permissions without creating a system role
        async with db_with_cleanup.begin_session() as db_sess:
            with pytest.raises(UserSystemRoleNotFound):
                await role_manager.add_object_permission_to_user_role(
                    db_sess, test_user_id, test_entity_id, [OperationType.READ]
                )

    @pytest.mark.asyncio
    async def test_add_permission_groups_only_adds_new_scopes(
        self,
        db_with_cleanup: ExtendedAsyncSAEngine,
        role_manager: RoleManager,
        test_user_and_system_role_id: tuple[uuid.UUID, uuid.UUID],
    ) -> None:
        """Test that adding permissions to a role with existing scope doesn't create duplicate permission groups."""
        # Given: System role with user (from fixture)
        user_id, role_id = test_user_and_system_role_id
        user_scope_id = ScopeId(scope_type=ScopeType.USER, scope_id=str(user_id))

        # Given: Create two entities in the same scope
        shared_scope_id = ScopeId(scope_type=ScopeType.PROJECT, scope_id=str(uuid.uuid4()))
        entity_id_1 = ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(uuid.uuid4()))
        entity_id_2 = ObjectId(entity_type=EntityType.VFOLDER, entity_id=str(uuid.uuid4()))

        async with db_with_cleanup.begin_session() as db_sess:
            await role_manager.map_entity_to_scope(db_sess, entity_id_1, shared_scope_id)
            await role_manager.map_entity_to_scope(db_sess, entity_id_2, shared_scope_id)

        # When: Add permissions for both entities
        async with db_with_cleanup.begin_session() as db_sess:
            await role_manager.add_object_permission_to_user_role(
                db_sess, user_id, entity_id_1, [OperationType.READ]
            )

        async with db_with_cleanup.begin_session() as db_sess:
            result = await role_manager.add_object_permission_to_user_role(
                db_sess, user_id, entity_id_2, [OperationType.UPDATE]
            )

        # Then: Verify only 2 permission groups exist (user scope + shared project scope)
        assert len(result.permission_groups) == 2
        scope_ids = {pg.scope_id for pg in result.permission_groups}
        assert scope_ids == {user_scope_id, shared_scope_id}
