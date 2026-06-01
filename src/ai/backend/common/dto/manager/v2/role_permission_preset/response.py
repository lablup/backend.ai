"""Response DTOs for role permission preset v2."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.rbac.types import OperationTypeDTO, RBACElementTypeDTO
from ai.backend.common.identifier.role_permission_preset import RolePermissionPresetID
from ai.backend.common.identifier.role_preset import RolePresetID

__all__ = (
    "BulkAddRolePermissionPresetsPayload",
    "BulkRemoveRolePermissionPresetsPayload",
    "BulkRolePermissionPresetFailureInfo",
    "RolePermissionPresetNode",
)


class RolePermissionPresetNode(BaseResponseModel):
    """Node model for a stored permission entry under a role preset."""

    id: RolePermissionPresetID = Field(description="Permission entry UUID.")
    role_preset_id: RolePresetID = Field(description="UUID of the parent role preset.")
    entity_type: RBACElementTypeDTO = Field(
        description="Entity type the permission applies to.",
    )
    operation: OperationTypeDTO = Field(description="Operation granted by the permission.")
    created_at: datetime = Field(description="Creation timestamp.")


class BulkRolePermissionPresetFailureInfo(BaseResponseModel):
    """Failure detail for a single role-permission-preset row in a bulk operation."""

    permission_preset_id: RolePermissionPresetID = Field(
        description="role_permission_presets row ID that the operation failed on.",
    )
    message: str = Field(description="Error message describing the failure.")


class BulkAddRolePermissionPresetsPayload(BaseResponseModel):
    """Payload for bulk-adding permission entries to a role preset."""

    permissions: list[RolePermissionPresetNode] = Field(
        description="Permission entries that were added.",
    )


class BulkRemoveRolePermissionPresetsPayload(BaseResponseModel):
    """Payload for bulk-removing permission entries from a role preset."""

    items: list[RolePermissionPresetNode] = Field(
        default_factory=list,
        description="Permission entries that were removed.",
    )
    failed: list[BulkRolePermissionPresetFailureInfo] = Field(
        default_factory=list,
        description="Permission entry IDs that failed to delete.",
    )
