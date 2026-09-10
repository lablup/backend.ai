from __future__ import annotations

import uuid
from typing import Any

import pytest

from ai.backend.common.data.entity.image import ImageEntityType
from ai.backend.common.data.entity.permission import PermissionID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.entity.vfolder import VFolderEntityType
from ai.backend.common.data.permission.types import OperationType, Permission
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.errors.common import ObjectNotFound
from ai.backend.manager.errors.permission import PermissionAlreadyGranted
from ai.backend.manager.models.rbac_models.permission.creators import RolePermissionCreator
from ai.backend.manager.models.rbac_models.permission.purgers import RolePermissionPurger
from ai.backend.manager.services.permission_contoller.actions.permission import (
    CreatePermissionAction,
    DeletePermissionAction,
)
from ai.backend.manager.services.permission_contoller.processors import (
    PermissionControllerProcessors,
)
from ai.backend.testutils.fixtures import DomainFixtureData


class TestPermissionCreate:
    """Permission CRUD — create operations at processor level."""

    async def test_create_basic_permission(
        self,
        permission_controller_processors: PermissionControllerProcessors,
        target_role: Any,
        domain_fixture: DomainFixtureData,
    ) -> None:
        """S-CREATE-1: Create basic permission with valid params → PermissionData returned."""
        creator = RolePermissionCreator(
            entity_type=EntityType(SessionEntityType()),
            permission=Permission.READ,
        )
        result = await permission_controller_processors.create_permission.wait_for_complete(
            CreatePermissionAction(role_id=RoleID(target_role.role.id), creator=creator)
        )

        assert isinstance(result.data, PermissionData)
        assert result.data.role_id == target_role.role.id
        assert result.data.entity_type == SessionEntityType()
        assert result.data.permission == Permission.READ

        # Cleanup
        await permission_controller_processors.delete_permission.wait_for_complete(
            DeletePermissionAction(purger=RolePermissionPurger(PermissionID(result.data.id)))
        )

    async def test_create_permissions_with_various_combinations(
        self,
        permission_controller_processors: PermissionControllerProcessors,
        target_role: Any,
        domain_fixture: DomainFixtureData,
    ) -> None:
        """S-CREATE-2: Create permissions with various scope/entity/operation combinations."""
        combos: list[tuple[EntityType, OperationType]] = [
            (SessionEntityType(), OperationType.READ),
            (ImageEntityType(), OperationType.UPDATE),
            (VFolderEntityType(), OperationType.SOFT_DELETE),
        ]
        created_ids: list[uuid.UUID] = []

        for entity_type, operation in combos:
            result = await permission_controller_processors.create_permission.wait_for_complete(
                CreatePermissionAction(
                    role_id=RoleID(target_role.role.id),
                    creator=RolePermissionCreator(
                        entity_type=EntityType(entity_type),
                        permission=Permission.from_operation(operation),
                    ),
                )
            )
            assert result.data.entity_type == entity_type
            assert result.data.permission == Permission.from_operation(operation)
            assert result.data.role_id == target_role.role.id
            created_ids.append(result.data.id)

        # Cleanup
        for perm_id in created_ids:
            await permission_controller_processors.delete_permission.wait_for_complete(
                DeletePermissionAction(purger=RolePermissionPurger(PermissionID(perm_id)))
            )

    async def test_create_duplicate_permission_raises_unique_constraint(
        self,
        permission_controller_processors: PermissionControllerProcessors,
        target_role: Any,
        domain_fixture: DomainFixtureData,
    ) -> None:
        """F-BIZ-4: Create duplicate permission → unique constraint error."""
        spec = RolePermissionCreator(
            entity_type=EntityType(VFolderEntityType()),
            permission=Permission.READ,
        )

        result = await permission_controller_processors.create_permission.wait_for_complete(
            CreatePermissionAction(role_id=RoleID(target_role.role.id), creator=spec)
        )
        perm_id = result.data.id

        try:
            with pytest.raises(PermissionAlreadyGranted):
                await permission_controller_processors.create_permission.wait_for_complete(
                    CreatePermissionAction(role_id=RoleID(target_role.role.id), creator=spec)
                )
        finally:
            await permission_controller_processors.delete_permission.wait_for_complete(
                DeletePermissionAction(purger=RolePermissionPurger(PermissionID(perm_id)))
            )


class TestPermissionDelete:
    """Permission CRUD — delete operations at processor level."""

    async def test_delete_existing_permission(
        self,
        permission_controller_processors: PermissionControllerProcessors,
        target_role: Any,
        domain_fixture: DomainFixtureData,
    ) -> None:
        """S-DELETE-1: Delete existing permission → deletion response."""
        create_result = await permission_controller_processors.create_permission.wait_for_complete(
            CreatePermissionAction(
                role_id=RoleID(target_role.role.id),
                creator=RolePermissionCreator(
                    entity_type=EntityType(SessionEntityType()),
                    permission=Permission.HARD_DELETE,
                ),
            )
        )
        perm_id = create_result.data.id

        delete_result = await permission_controller_processors.delete_permission.wait_for_complete(
            DeletePermissionAction(purger=RolePermissionPurger(PermissionID(perm_id)))
        )

        assert isinstance(delete_result.data, PermissionData)
        assert delete_result.data.id == perm_id

    async def test_deleted_permission_no_longer_exists(
        self,
        permission_controller_processors: PermissionControllerProcessors,
        target_role: Any,
        domain_fixture: DomainFixtureData,
    ) -> None:
        """S-DELETE-2: Verify deleted permission no longer exists."""
        create_result = await permission_controller_processors.create_permission.wait_for_complete(
            CreatePermissionAction(
                role_id=RoleID(target_role.role.id),
                creator=RolePermissionCreator(
                    entity_type=EntityType(ImageEntityType()),
                    permission=Permission.SOFT_DELETE,
                ),
            )
        )
        perm_id = create_result.data.id

        await permission_controller_processors.delete_permission.wait_for_complete(
            DeletePermissionAction(purger=RolePermissionPurger(PermissionID(perm_id)))
        )

        # Second delete must raise ObjectNotFound
        with pytest.raises(ObjectNotFound):
            await permission_controller_processors.delete_permission.wait_for_complete(
                DeletePermissionAction(purger=RolePermissionPurger(PermissionID(perm_id)))
            )

    async def test_delete_nonexistent_permission_raises_not_found(
        self,
        permission_controller_processors: PermissionControllerProcessors,
    ) -> None:
        """F-BIZ-2: Delete non-existent permission_id → ObjectNotFound."""
        with pytest.raises(ObjectNotFound):
            await permission_controller_processors.delete_permission.wait_for_complete(
                DeletePermissionAction(purger=RolePermissionPurger(PermissionID(uuid.uuid4())))
            )
