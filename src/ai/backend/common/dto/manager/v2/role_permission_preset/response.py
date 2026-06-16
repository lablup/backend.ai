"""Response DTOs for role permission preset v2."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.rbac.types import OperationTypeDTO, RBACElementTypeDTO
from ai.backend.common.identifier.role_permission_preset import RolePermissionPresetID
from ai.backend.common.identifier.role_preset import RolePresetID

__all__ = (
    "BulkAddRolePermissionPresetFailureInfo",
    "BulkAddRolePermissionPresetsPayload",
    "BulkRemoveRolePermissionPresetsPayload",
    "BulkRolePermissionPresetFailureInfo",
    "RolePermissionPresetNode",
    "SearchRolePermissionPresetsPayload",
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


class SearchRolePermissionPresetsPayload(BaseResponseModel):
    """Payload for paginated permission-entry search under a role preset."""

    items: list[RolePermissionPresetNode] = Field(
        description="Permission entry nodes matching the filter."
    )
    total_count: int = Field(description="Total number matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")


class BulkRolePermissionPresetFailureInfo(BaseResponseModel):
    """Failure detail for a single role-permission-preset row in a bulk operation."""

    permission_preset_id: RolePermissionPresetID = Field(
        description="role_permission_presets row ID that the operation failed on.",
    )
    message: str = Field(description="Error message describing the failure.")


class BulkAddRolePermissionPresetFailureInfo(BaseResponseModel):
    """Failure detail for a single permission entry in a bulk add operation.

    Added entries have no row ID yet, so failures are keyed by the
    ``(entity_type, operation)`` pair that could not be inserted (e.g., a duplicate).
    """

    entity_type: RBACElementTypeDTO = Field(
        description="Entity type of the permission entry that failed.",
    )
    operation: OperationTypeDTO = Field(
        description="Operation of the permission entry that failed.",
    )
    message: str = Field(description="Error message describing the failure.")


class BulkAddRolePermissionPresetsPayload(BaseResponseModel):
    """Payload for bulk-adding permission entries to a role preset."""

    items: list[RolePermissionPresetNode] = Field(
        default_factory=list,
        description="Permission entries that were added.",
    )
    failed: list[BulkAddRolePermissionPresetFailureInfo] = Field(
        default_factory=list,
        description="Permission entries that failed to be added (e.g., duplicates).",
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
