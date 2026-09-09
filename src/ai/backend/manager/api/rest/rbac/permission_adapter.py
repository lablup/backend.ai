"""
Adapter for Permission RBAC operations.
Converts between API DTOs and service layer actions.
"""

from __future__ import annotations

import uuid

from ai.backend.common.data.entity.permission import PermissionID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.rbac import (
    CreatePermissionRequest,
    PermissionDTO,
)
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.models.rbac_models.permission.creators import RolePermissionCreator
from ai.backend.manager.models.rbac_models.permission.purgers import RolePermissionPurger
from ai.backend.manager.services.permission_contoller.actions.permission import (
    CreatePermissionAction,
    DeletePermissionAction,
)

__all__ = ("PermissionAdapter",)


class PermissionAdapter:
    """Adapter for converting permission requests to actions and data to DTOs."""

    @staticmethod
    def to_permission_dto(data: PermissionData) -> PermissionDTO:
        """Convert PermissionData to PermissionDTO."""
        return PermissionDTO(
            id=data.id,
            entity_type=data.entity_type,
            operation=data.permission.to_operation(),
        )

    @staticmethod
    def to_create_permission_action(request: CreatePermissionRequest) -> CreatePermissionAction:
        """Convert CreatePermissionRequest to CreatePermissionAction."""
        creator = RolePermissionCreator(
            entity_type=EntityType(request.entity_type),
            permission=Permission.from_operation(request.operation),
        )
        return CreatePermissionAction(role_id=RoleID(request.role_id), creator=creator)

    @staticmethod
    def to_delete_permission_action(permission_id: uuid.UUID) -> DeletePermissionAction:
        """Convert permission_id to DeletePermissionAction."""
        return DeletePermissionAction(purger=RolePermissionPurger(PermissionID(permission_id)))
