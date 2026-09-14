"""
Adapter for Permission RBAC operations.
Converts between API DTOs and service layer actions.
"""

from __future__ import annotations

import uuid

from ai.backend.common.data.entity.permission import PermissionID
from ai.backend.common.data.entity.role import RoleID
from ai.backend.common.dto.manager.rbac import (
    CreatePermissionRequest,
    PermissionDTO,
)
from ai.backend.common.dto.manager.v2.rbac.types import PermissionBitDTO
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
            permission=PermissionBitDTO.of(data.permission),
        )

    @staticmethod
    def to_create_permission_action(request: CreatePermissionRequest) -> CreatePermissionAction:
        """Convert CreatePermissionRequest to CreatePermissionAction."""
        creator = RolePermissionCreator(
            entity_type=request.entity_type,
            permission=request.permission.to_permission(),
        )
        return CreatePermissionAction(role_id=RoleID(request.role_id), creator=creator)

    @staticmethod
    def to_delete_permission_action(permission_id: uuid.UUID) -> DeletePermissionAction:
        """Convert permission_id to DeletePermissionAction."""
        return DeletePermissionAction(purger=RolePermissionPurger(PermissionID(permission_id)))
