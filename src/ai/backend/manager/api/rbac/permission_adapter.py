"""
Adapter for Permission RBAC operations.
Converts between API DTOs and service layer actions.
"""

from __future__ import annotations

import uuid

from ai.backend.common.dto.manager.rbac import (
    CreatePermissionRequest,
    PermissionDTO,
)
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.repositories.base import Creator, Purger
from ai.backend.manager.repositories.permission_controller.creators import (
    PermissionCreatorSpec,
)
from ai.backend.manager.services.permission_contoller.actions.permission import (
    CreatePermissionAction,
    DeletePermissionAction,
)

from ...models.rbac_models.permission.permission import PermissionRow

__all__ = ("PermissionAdapter",)


class PermissionAdapter:
    """Adapter for converting permission requests to actions and data to DTOs."""

    @staticmethod
    def to_permission_dto(data: PermissionData) -> PermissionDTO:
        """Convert PermissionData to PermissionDTO."""
        return PermissionDTO(
            id=data.id,
            permission_group_id=data.permission_group_id,
            entity_type=data.entity_type,
            operation=data.operation,
        )

    @staticmethod
    def to_create_permission_action(request: CreatePermissionRequest) -> CreatePermissionAction:
        """Convert CreatePermissionRequest to CreatePermissionAction."""
        creator = Creator(
            spec=PermissionCreatorSpec(
                permission_group_id=request.permission_group_id,
                entity_type=request.entity_type,
                operation=request.operation,
            )
        )
        return CreatePermissionAction(creator=creator)

    @staticmethod
    def to_delete_permission_action(permission_id: uuid.UUID) -> DeletePermissionAction:
        """Convert permission_id to DeletePermissionAction."""
        purger = Purger(row_class=PermissionRow, pk_value=permission_id)
        return DeletePermissionAction(purger=purger)
