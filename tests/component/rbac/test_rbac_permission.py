from __future__ import annotations

import uuid
from typing import Any

import pytest

from ai.backend.common.data.permission.types import GLOBAL_SCOPE_ID, OperationType, ScopeType
from ai.backend.manager.data.permission.id import ObjectId, ScopeId
from ai.backend.manager.data.permission.object_permission import ObjectPermissionData
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.data.permission.role import (
    BatchEntityPermissionCheckInput,
    ScopePermissionCheckInput,
    SingleEntityPermissionCheckInput,
    UserRoleAssignmentInput,
    UserRoleRevocationInput,
)
from ai.backend.manager.data.permission.types import EntityType
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.errors.repository import (
    ForeignKeyViolationError,
    UniqueConstraintViolationError,
)
from ai.backend.manager.models.rbac_models.permission.object_permission import ObjectPermissionRow
from ai.backend.manager.models.rbac_models.permission.permission import PermissionRow
from ai.backend.manager.models.utils import ExtendedAsyncSAEngine
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.repositories.base.purger import Purger
from ai.backend.manager.repositories.permission_controller.creators import (
    ObjectPermissionCreatorSpec,
    PermissionCreatorSpec,
)
from ai.backend.manager.repositories.permission_controller.repository import (
    PermissionControllerRepository,
)
from ai.backend.manager.services.permission_contoller.actions.assign_role import AssignRoleAction
from ai.backend.manager.services.permission_contoller.actions.object_permission import (
    CreateObjectPermissionAction,
    DeleteObjectPermissionAction,
)
from ai.backend.manager.services.permission_contoller.actions.permission import (
    CreatePermissionAction,
    DeletePermissionAction,
)
from ai.backend.manager.services.permission_contoller.actions.revoke_role import RevokeRoleAction
from ai.backend.manager.services.permission_contoller.processors import (
    PermissionControllerProcessors,
)
from ai.backend.manager.services.permission_contoller.service import PermissionControllerService

from .conftest import RoleFactory


@pytest.fixture()
def permission_service(database_engine: ExtendedAsyncSAEngine) -> PermissionControllerService:
    """Direct service fixture for operations not exposed through processors."""
    repo = PermissionControllerRepository(database_engine)
    return PermissionControllerService(repo)


@pytest.fixture()
def permission_repo(database_engine: ExtendedAsyncSAEngine) -> PermissionControllerRepository:
    """Direct repository fixture for check-permission operations."""
    return PermissionControllerRepository(database_engine)


class TestPermissionCreate:
    """Permission CRUD — create operations at processor level."""

    async def test_create_basic_permission(
        self,
        permission_controller_processors: PermissionControllerProcessors,
        target_role: Any,
    ) -> None:
        """S-CREATE-1: Create basic permission with valid params → PermissionData returned."""
        creator = Creator(
            spec=PermissionCreatorSpec(
                role_id=target_role.role.id,
                scope_type=ScopeType.GLOBAL,
                scope_id=GLOBAL_SCOPE_ID,
                entity_type=EntityType.SESSION,
                operation=OperationType.READ,
            )
        )
        result = await permission_controller_processors.create_permission.wait_for_complete(
            CreatePermissionAction(creator=creator)
        )

        assert isinstance(result.data, PermissionData)
        assert result.data.role_id == target_role.role.id
        assert result.data.scope_type == ScopeType.GLOBAL
        assert result.data.entity_type == EntityType.SESSION
        assert result.data.operation == OperationType.READ

        # Cleanup
        await permission_controller_processors.delete_permission.wait_for_complete(
            DeletePermissionAction(purger=Purger(row_class=PermissionRow, pk_value=result.data.id))
        )

    async def test_create_permissions_with_various_combinations(
        self,
        permission_controller_processors: PermissionControllerProcessors,
        target_role: Any,
    ) -> None:
        """S-CREATE-2: Create permissions with various scope/entity/operation combinations."""
        combos: list[tuple[ScopeType, str, EntityType, OperationType]] = [
            (ScopeType.GLOBAL, GLOBAL_SCOPE_ID, EntityType.SESSION, OperationType.READ),
            (ScopeType.GLOBAL, GLOBAL_SCOPE_ID, EntityType.IMAGE, OperationType.UPDATE),
            (ScopeType.GLOBAL, GLOBAL_SCOPE_ID, EntityType.VFOLDER, OperationType.SOFT_DELETE),
        ]
        created_ids: list[uuid.UUID] = []

        for scope_type, scope_id, entity_type, operation in combos:
            result = await permission_controller_processors.create_permission.wait_for_complete(
                CreatePermissionAction(
                    creator=Creator(
                        spec=PermissionCreatorSpec(
                            role_id=target_role.role.id,
                            scope_type=scope_type,
                            scope_id=scope_id,
                            entity_type=entity_type,
                            operation=operation,
                        )
                    )
                )
            )
            assert result.data.entity_type == entity_type
            assert result.data.operation == operation
            assert result.data.role_id == target_role.role.id
            created_ids.append(result.data.id)

        # Cleanup
        for perm_id in created_ids:
            await permission_controller_processors.delete_permission.wait_for_complete(
                DeletePermissionAction(purger=Purger(row_class=PermissionRow, pk_value=perm_id))
            )

    async def test_create_duplicate_permission_raises_unique_constraint(
        self,
        permission_controller_processors: PermissionControllerProcessors,
        target_role: Any,
    ) -> None:
        """F-BIZ-4: Create duplicate permission → unique constraint error."""
        spec = PermissionCreatorSpec(
            role_id=target_role.role.id,
            scope_type=ScopeType.GLOBAL,
            scope_id=GLOBAL_SCOPE_ID,
            entity_type=EntityType.VFOLDER,
            operation=OperationType.READ,
        )

        result = await permission_controller_processors.create_permission.wait_for_complete(
            CreatePermissionAction(creator=Creator(spec=spec))
        )
        perm_id = result.data.id

        try:
            with pytest.raises(UniqueConstraintViolationError):
                await permission_controller_processors.create_permission.wait_for_complete(
                    CreatePermissionAction(creator=Creator(spec=spec))
                )
        finally:
            await permission_controller_processors.delete_permission.wait_for_complete(
                DeletePermissionAction(purger=Purger(row_class=PermissionRow, pk_value=perm_id))
            )


class TestPermissionDelete:
    """Permission CRUD — delete operations at processor level."""

    async def test_delete_existing_permission(
        self,
        permission_controller_processors: PermissionControllerProcessors,
        target_role: Any,
    ) -> None:
        """S-DELETE-1: Delete existing permission → deletion response."""
        create_result = await permission_controller_processors.create_permission.wait_for_complete(
            CreatePermissionAction(
                creator=Creator(
                    spec=PermissionCreatorSpec(
                        role_id=target_role.role.id,
                        scope_type=ScopeType.GLOBAL,
                        scope_id=GLOBAL_SCOPE_ID,
                        entity_type=EntityType.SESSION,
                        operation=OperationType.HARD_DELETE,
                    )
                )
            )
        )
        perm_id = create_result.data.id

        delete_result = await permission_controller_processors.delete_permission.wait_for_complete(
            DeletePermissionAction(purger=Purger(row_class=PermissionRow, pk_value=perm_id))
        )

        assert isinstance(delete_result.data, PermissionData)
        assert delete_result.data.id == perm_id

    async def test_deleted_permission_no_longer_exists(
        self,
        permission_controller_processors: PermissionControllerProcessors,
        target_role: Any,
    ) -> None:
        """S-DELETE-2: Verify deleted permission no longer exists."""
        create_result = await permission_controller_processors.create_permission.wait_for_complete(
            CreatePermissionAction(
                creator=Creator(
                    spec=PermissionCreatorSpec(
                        role_id=target_role.role.id,
                        scope_type=ScopeType.GLOBAL,
                        scope_id=GLOBAL_SCOPE_ID,
                        entity_type=EntityType.IMAGE,
                        operation=OperationType.SOFT_DELETE,
                    )
                )
            )
        )
        perm_id = create_result.data.id

        await permission_controller_processors.delete_permission.wait_for_complete(
            DeletePermissionAction(purger=Purger(row_class=PermissionRow, pk_value=perm_id))
        )

        # Second delete must raise ObjectNotFound
        with pytest.raises(ObjectNotFound):
            await permission_controller_processors.delete_permission.wait_for_complete(
                DeletePermissionAction(purger=Purger(row_class=PermissionRow, pk_value=perm_id))
            )

    async def test_delete_nonexistent_permission_raises_not_found(
        self,
        permission_controller_processors: PermissionControllerProcessors,
    ) -> None:
        """F-BIZ-2: Delete non-existent permission_id → ObjectNotFound."""
        with pytest.raises(ObjectNotFound):
            await permission_controller_processors.delete_permission.wait_for_complete(
                DeletePermissionAction(
                    purger=Purger(row_class=PermissionRow, pk_value=uuid.uuid4())
                )
            )


class TestObjectPermissionCreate:
    """ObjectPermission — create operations at service level."""

    async def test_create_object_permission(
        self,
        permission_service: PermissionControllerService,
        target_role: Any,
    ) -> None:
        """S-CREATE-1: Create ObjectPermission with valid params → ObjectPermissionData."""
        entity_id = str(uuid.uuid4())
        result = await permission_service.create_object_permission(
            CreateObjectPermissionAction(
                creator=Creator(
                    spec=ObjectPermissionCreatorSpec(
                        role_id=target_role.role.id,
                        entity_type=EntityType.SESSION,
                        entity_id=entity_id,
                        operation=OperationType.READ,
                    )
                )
            )
        )

        assert isinstance(result.data, ObjectPermissionData)
        assert result.data.role_id == target_role.role.id
        assert result.data.object_id.entity_type == EntityType.SESSION
        assert result.data.object_id.entity_id == entity_id
        assert result.data.operation == OperationType.READ

        # Cleanup
        await permission_service.delete_object_permission(
            DeleteObjectPermissionAction(
                purger=Purger(row_class=ObjectPermissionRow, pk_value=result.data.id)
            )
        )

    async def test_create_multiple_object_permissions_for_same_role(
        self,
        permission_service: PermissionControllerService,
        target_role: Any,
    ) -> None:
        """S-CREATE-2: Create multiple ObjectPermissions for a role → each correctly stored."""
        entity_ids = [str(uuid.uuid4()) for _ in range(2)]
        created_ids: list[uuid.UUID] = []

        for entity_id in entity_ids:
            result = await permission_service.create_object_permission(
                CreateObjectPermissionAction(
                    creator=Creator(
                        spec=ObjectPermissionCreatorSpec(
                            role_id=target_role.role.id,
                            entity_type=EntityType.VFOLDER,
                            entity_id=entity_id,
                            operation=OperationType.READ,
                        )
                    )
                )
            )
            assert result.data.role_id == target_role.role.id
            assert result.data.object_id.entity_id == entity_id
            created_ids.append(result.data.id)

        # Cleanup
        for obj_perm_id in created_ids:
            await permission_service.delete_object_permission(
                DeleteObjectPermissionAction(
                    purger=Purger(row_class=ObjectPermissionRow, pk_value=obj_perm_id)
                )
            )

    async def test_create_object_permission_with_nonexistent_role_raises_fk_error(
        self,
        permission_service: PermissionControllerService,
    ) -> None:
        """F-BIZ-2: Create ObjectPermission with non-existent role_id → FK violation error."""
        with pytest.raises(ForeignKeyViolationError):
            await permission_service.create_object_permission(
                CreateObjectPermissionAction(
                    creator=Creator(
                        spec=ObjectPermissionCreatorSpec(
                            role_id=uuid.uuid4(),  # non-existent role
                            entity_type=EntityType.SESSION,
                            entity_id=str(uuid.uuid4()),
                            operation=OperationType.READ,
                        )
                    )
                )
            )


class TestObjectPermissionDelete:
    """ObjectPermission — delete operations at service level."""

    async def test_delete_object_permission(
        self,
        permission_service: PermissionControllerService,
        target_role: Any,
    ) -> None:
        """S-DELETE-1: Delete ObjectPermission → deletion response with data."""
        entity_id = str(uuid.uuid4())
        create_result = await permission_service.create_object_permission(
            CreateObjectPermissionAction(
                creator=Creator(
                    spec=ObjectPermissionCreatorSpec(
                        role_id=target_role.role.id,
                        entity_type=EntityType.IMAGE,
                        entity_id=entity_id,
                        operation=OperationType.READ,
                    )
                )
            )
        )
        obj_perm_id = create_result.data.id

        delete_result = await permission_service.delete_object_permission(
            DeleteObjectPermissionAction(
                purger=Purger(row_class=ObjectPermissionRow, pk_value=obj_perm_id)
            )
        )

        assert isinstance(delete_result.data, ObjectPermissionData)
        assert delete_result.data.id == obj_perm_id

    async def test_delete_nonexistent_object_permission_returns_none(
        self,
        permission_service: PermissionControllerService,
    ) -> None:
        """F-BIZ-1: Delete non-existent object_permission_id → result with data=None."""
        result = await permission_service.delete_object_permission(
            DeleteObjectPermissionAction(
                purger=Purger(row_class=ObjectPermissionRow, pk_value=uuid.uuid4())
            )
        )

        assert result.data is None


class TestCheckPermissionOfEntity:
    """Check permission of a specific entity (object-level check)."""

    async def test_user_with_matching_object_permission_returns_true(
        self,
        permission_controller_processors: PermissionControllerProcessors,
        permission_service: PermissionControllerService,
        permission_repo: PermissionControllerRepository,
        role_factory: RoleFactory,
        admin_user_fixture: Any,
    ) -> None:
        """S-ENTITY-1: User with matching role+ObjectPermission → True."""
        role = await role_factory()
        role_id = role.role.id
        user_id: uuid.UUID = admin_user_fixture.user_uuid
        entity_id = str(uuid.uuid4())

        # Create a scoped permission (required for get_user_roles JOIN)
        perm_result = await permission_controller_processors.create_permission.wait_for_complete(
            CreatePermissionAction(
                creator=Creator(
                    spec=PermissionCreatorSpec(
                        role_id=role_id,
                        scope_type=ScopeType.GLOBAL,
                        scope_id=GLOBAL_SCOPE_ID,
                        entity_type=EntityType.SESSION,
                        operation=OperationType.READ,
                    )
                )
            )
        )

        # Create an object permission for the user's entity
        obj_perm_result = await permission_service.create_object_permission(
            CreateObjectPermissionAction(
                creator=Creator(
                    spec=ObjectPermissionCreatorSpec(
                        role_id=role_id,
                        entity_type=EntityType.SESSION,
                        entity_id=entity_id,
                        operation=OperationType.READ,
                    )
                )
            )
        )

        # Assign the role to the user
        await permission_controller_processors.assign_role.wait_for_complete(
            AssignRoleAction(input=UserRoleAssignmentInput(user_id=user_id, role_id=role_id))
        )

        try:
            has_perm = await permission_repo.check_permission_of_entity(
                SingleEntityPermissionCheckInput(
                    user_id=user_id,
                    target_object_id=ObjectId(entity_type=EntityType.SESSION, entity_id=entity_id),
                    operation=OperationType.READ,
                )
            )
            assert has_perm is True
        finally:
            # Cleanup
            await permission_controller_processors.revoke_role.wait_for_complete(
                RevokeRoleAction(input=UserRoleRevocationInput(user_id=user_id, role_id=role_id))
            )
            await permission_service.delete_object_permission(
                DeleteObjectPermissionAction(
                    purger=Purger(row_class=ObjectPermissionRow, pk_value=obj_perm_result.data.id)
                )
            )
            await permission_controller_processors.delete_permission.wait_for_complete(
                DeletePermissionAction(
                    purger=Purger(row_class=PermissionRow, pk_value=perm_result.data.id)
                )
            )

    async def test_user_without_matching_object_permission_returns_false(
        self,
        permission_controller_processors: PermissionControllerProcessors,
        permission_service: PermissionControllerService,
        permission_repo: PermissionControllerRepository,
        role_factory: RoleFactory,
        admin_user_fixture: Any,
    ) -> None:
        """S-ENTITY-2: User without matching ObjectPermission → False."""
        role = await role_factory()
        role_id = role.role.id
        user_id: uuid.UUID = admin_user_fixture.user_uuid
        checked_entity_id = str(uuid.uuid4())
        other_entity_id = str(uuid.uuid4())

        # Create scoped permission (for get_user_roles JOIN)
        perm_result = await permission_controller_processors.create_permission.wait_for_complete(
            CreatePermissionAction(
                creator=Creator(
                    spec=PermissionCreatorSpec(
                        role_id=role_id,
                        scope_type=ScopeType.GLOBAL,
                        scope_id=GLOBAL_SCOPE_ID,
                        entity_type=EntityType.SESSION,
                        operation=OperationType.READ,
                    )
                )
            )
        )

        # Create object permission for a DIFFERENT entity (not the one we'll check)
        obj_perm_result = await permission_service.create_object_permission(
            CreateObjectPermissionAction(
                creator=Creator(
                    spec=ObjectPermissionCreatorSpec(
                        role_id=role_id,
                        entity_type=EntityType.SESSION,
                        entity_id=other_entity_id,
                        operation=OperationType.READ,
                    )
                )
            )
        )

        await permission_controller_processors.assign_role.wait_for_complete(
            AssignRoleAction(input=UserRoleAssignmentInput(user_id=user_id, role_id=role_id))
        )

        try:
            has_perm = await permission_repo.check_permission_of_entity(
                SingleEntityPermissionCheckInput(
                    user_id=user_id,
                    target_object_id=ObjectId(
                        entity_type=EntityType.SESSION, entity_id=checked_entity_id
                    ),
                    operation=OperationType.READ,
                )
            )
            assert has_perm is False
        finally:
            await permission_controller_processors.revoke_role.wait_for_complete(
                RevokeRoleAction(input=UserRoleRevocationInput(user_id=user_id, role_id=role_id))
            )
            await permission_service.delete_object_permission(
                DeleteObjectPermissionAction(
                    purger=Purger(row_class=ObjectPermissionRow, pk_value=obj_perm_result.data.id)
                )
            )
            await permission_controller_processors.delete_permission.wait_for_complete(
                DeletePermissionAction(
                    purger=Purger(row_class=PermissionRow, pk_value=perm_result.data.id)
                )
            )

    async def test_user_with_no_roles_returns_false(
        self,
        permission_repo: PermissionControllerRepository,
    ) -> None:
        """S-ENTITY-3: User with no roles → False."""
        has_perm = await permission_repo.check_permission_of_entity(
            SingleEntityPermissionCheckInput(
                user_id=uuid.uuid4(),  # random user with no roles
                target_object_id=ObjectId(
                    entity_type=EntityType.SESSION, entity_id=str(uuid.uuid4())
                ),
                operation=OperationType.READ,
            )
        )
        assert has_perm is False


class TestCheckPermissionInScope:
    """Check permission within a specific scope (scope-level check)."""

    async def test_user_with_permission_in_scope_returns_true(
        self,
        permission_controller_processors: PermissionControllerProcessors,
        permission_repo: PermissionControllerRepository,
        role_factory: RoleFactory,
        admin_user_fixture: Any,
    ) -> None:
        """S-SCOPE-1: User has permission in target scope → True."""
        role = await role_factory()
        role_id = role.role.id
        user_id: uuid.UUID = admin_user_fixture.user_uuid

        perm_result = await permission_controller_processors.create_permission.wait_for_complete(
            CreatePermissionAction(
                creator=Creator(
                    spec=PermissionCreatorSpec(
                        role_id=role_id,
                        scope_type=ScopeType.GLOBAL,
                        scope_id=GLOBAL_SCOPE_ID,
                        entity_type=EntityType.SESSION,
                        operation=OperationType.READ,
                    )
                )
            )
        )

        await permission_controller_processors.assign_role.wait_for_complete(
            AssignRoleAction(input=UserRoleAssignmentInput(user_id=user_id, role_id=role_id))
        )

        try:
            has_perm = await permission_repo.check_permission_in_scope(
                ScopePermissionCheckInput(
                    user_id=user_id,
                    target_entity_type=EntityType.SESSION,
                    target_scope_id=ScopeId(scope_type=ScopeType.GLOBAL, scope_id=GLOBAL_SCOPE_ID),
                    operation=OperationType.READ,
                )
            )
            assert has_perm is True
        finally:
            await permission_controller_processors.revoke_role.wait_for_complete(
                RevokeRoleAction(input=UserRoleRevocationInput(user_id=user_id, role_id=role_id))
            )
            await permission_controller_processors.delete_permission.wait_for_complete(
                DeletePermissionAction(
                    purger=Purger(row_class=PermissionRow, pk_value=perm_result.data.id)
                )
            )

    async def test_user_without_permission_in_scope_returns_false(
        self,
        permission_repo: PermissionControllerRepository,
    ) -> None:
        """S-SCOPE-2: User lacks permission in target scope → False."""
        has_perm = await permission_repo.check_permission_in_scope(
            ScopePermissionCheckInput(
                user_id=uuid.uuid4(),  # random user with no roles
                target_entity_type=EntityType.SESSION,
                target_scope_id=ScopeId(scope_type=ScopeType.GLOBAL, scope_id=GLOBAL_SCOPE_ID),
                operation=OperationType.READ,
            )
        )
        assert has_perm is False


class TestCheckPermissionBatch:
    """Batch permission check across multiple entities."""

    async def test_batch_check_returns_correct_mapping(
        self,
        permission_controller_processors: PermissionControllerProcessors,
        permission_service: PermissionControllerService,
        permission_repo: PermissionControllerRepository,
        role_factory: RoleFactory,
        admin_user_fixture: Any,
    ) -> None:
        """S-BATCH-1: Batch check returns correct per-object bool mapping."""
        role = await role_factory()
        role_id = role.role.id
        user_id: uuid.UUID = admin_user_fixture.user_uuid

        entity_id_with_perm = str(uuid.uuid4())
        entity_id_without_perm = str(uuid.uuid4())

        # Create scoped permission (for get_user_roles JOIN in entity check)
        perm_result = await permission_controller_processors.create_permission.wait_for_complete(
            CreatePermissionAction(
                creator=Creator(
                    spec=PermissionCreatorSpec(
                        role_id=role_id,
                        scope_type=ScopeType.GLOBAL,
                        scope_id=GLOBAL_SCOPE_ID,
                        entity_type=EntityType.SESSION,
                        operation=OperationType.READ,
                    )
                )
            )
        )

        # Create object permission for ONE entity only
        obj_perm_result = await permission_service.create_object_permission(
            CreateObjectPermissionAction(
                creator=Creator(
                    spec=ObjectPermissionCreatorSpec(
                        role_id=role_id,
                        entity_type=EntityType.SESSION,
                        entity_id=entity_id_with_perm,
                        operation=OperationType.READ,
                    )
                )
            )
        )

        await permission_controller_processors.assign_role.wait_for_complete(
            AssignRoleAction(input=UserRoleAssignmentInput(user_id=user_id, role_id=role_id))
        )

        try:
            target_ids = [
                ObjectId(entity_type=EntityType.SESSION, entity_id=entity_id_with_perm),
                ObjectId(entity_type=EntityType.SESSION, entity_id=entity_id_without_perm),
            ]
            result = await permission_repo.check_permission_of_entities(
                BatchEntityPermissionCheckInput(
                    user_id=user_id,
                    target_object_ids=target_ids,
                    operation=OperationType.READ,
                )
            )
            assert result[ObjectId(EntityType.SESSION, entity_id_with_perm)] is True
            assert result[ObjectId(EntityType.SESSION, entity_id_without_perm)] is False
        finally:
            await permission_controller_processors.revoke_role.wait_for_complete(
                RevokeRoleAction(input=UserRoleRevocationInput(user_id=user_id, role_id=role_id))
            )
            await permission_service.delete_object_permission(
                DeleteObjectPermissionAction(
                    purger=Purger(row_class=ObjectPermissionRow, pk_value=obj_perm_result.data.id)
                )
            )
            await permission_controller_processors.delete_permission.wait_for_complete(
                DeletePermissionAction(
                    purger=Purger(row_class=PermissionRow, pk_value=perm_result.data.id)
                )
            )

    async def test_batch_check_with_empty_list_returns_empty_mapping(
        self,
        permission_repo: PermissionControllerRepository,
    ) -> None:
        """S-BATCH-4: Empty entity list → empty mapping."""
        result = await permission_repo.check_permission_of_entities(
            BatchEntityPermissionCheckInput(
                user_id=uuid.uuid4(),
                target_object_ids=[],
                operation=OperationType.READ,
            )
        )
        assert result == {}
