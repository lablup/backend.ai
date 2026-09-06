"""
Adapter for Permission RBAC operations.
Converts between API DTOs and service layer actions.
"""

from __future__ import annotations

import uuid

from ai.backend.common.data.entity.types import EntityType, ScopeType
from ai.backend.common.data.permission.types import Permission
from ai.backend.common.dto.manager.rbac import (
    CreatePermissionRequest,
    PermissionDTO,
)
from ai.backend.manager.data.permission.bit import single_bit
from ai.backend.manager.data.permission.permission import PermissionData
from ai.backend.manager.repositories.base import Creator, Purger
from ai.backend.manager.repositories.permission_controller.creators import (
    PermissionCreatorSpec,
)
from ai.backend.manager.repositories.permission_controller.purgers import PermissionPurgerSpec
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
        creator = Creator(
            spec=PermissionCreatorSpec(
                role_id=request.role_id,
                scope_type=ScopeType(EntityType(request.scope_type)),
                scope_id=request.scope_id,
                entity_type=EntityType(request.entity_type),
                permission=single_bit(Permission.from_operation(request.operation)),
            )
        )
        return CreatePermissionAction(creator=creator)

    @staticmethod
    def to_delete_permission_action(permission_id: uuid.UUID) -> DeletePermissionAction:
        """Convert permission_id to DeletePermissionAction."""
        purger = Purger(spec=PermissionPurgerSpec(permission_id=permission_id))
        return DeletePermissionAction(purger=purger)
