"""
Adapter for ObjectPermission RBAC operations.
Converts between API DTOs and service layer actions.
"""

from __future__ import annotations

import uuid

from ai.backend.common.dto.manager.rbac import (
    CreateObjectPermissionRequest,
    ObjectPermissionDTO,
)
from ai.backend.manager.data.permission.object_permission import ObjectPermissionData
from ai.backend.manager.repositories.base import Creator, Purger
from ai.backend.manager.repositories.permission_controller.creators import (
    ObjectPermissionCreatorSpec,
)
from ai.backend.manager.services.permission_contoller.actions.object_permission import (
    CreateObjectPermissionAction,
    DeleteObjectPermissionAction,
)

from ...models.rbac_models.permission.object_permission import ObjectPermissionRow

__all__ = ("ObjectPermissionAdapter",)


class ObjectPermissionAdapter:
    """Adapter for converting object permission requests to actions and data to DTOs."""

    def to_object_permission_dto(self, data: ObjectPermissionData) -> ObjectPermissionDTO:
        """Convert ObjectPermissionData to ObjectPermissionDTO."""
        return ObjectPermissionDTO(
            id=data.id,
            role_id=data.role_id,
            entity_type=data.object_id.entity_type,
            entity_id=data.object_id.entity_id,
            operation=data.operation,
        )

    def to_create_object_permission_action(
        self,
        request: CreateObjectPermissionRequest,
    ) -> CreateObjectPermissionAction:
        """Convert CreateObjectPermissionRequest to CreateObjectPermissionAction."""
        creator = Creator(
            spec=ObjectPermissionCreatorSpec(
                role_id=request.role_id,
                entity_type=request.entity_type,
                entity_id=request.entity_id,
                operation=request.operation,
                status=request.status,
            )
        )
        return CreateObjectPermissionAction(creator=creator)

    def to_delete_object_permission_action(
        self,
        object_permission_id: uuid.UUID,
    ) -> DeleteObjectPermissionAction:
        """Convert object_permission_id to DeleteObjectPermissionAction."""
        purger = Purger(row_class=ObjectPermissionRow, pk_value=object_permission_id)
        return DeleteObjectPermissionAction(purger=purger)
