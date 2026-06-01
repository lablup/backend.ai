"""Response DTOs for role preset v2."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.rbac.types import RBACElementTypeDTO
from ai.backend.common.identifier.role_preset import RolePresetID

__all__ = (
    "BulkDeleteRolePresetsPayload",
    "BulkPurgeRolePresetsPayload",
    "BulkRestoreRolePresetsPayload",
    "BulkRolePresetFailureInfo",
    "CreateRolePresetPayload",
    "RolePresetNode",
    "SearchRolePresetsPayload",
    "UpdateRolePresetPayload",
)


class RolePresetNode(BaseResponseModel):
    """Node model representing a role preset entity.

    Permission entries are resolved separately (e.g., via a GraphQL `permissions` field
    backed by a data loader, or a dedicated REST endpoint) and are not embedded here.
    """

    id: RolePresetID = Field(description="Role preset UUID.")
    name: str = Field(description="Role preset name.")
    scope_type: RBACElementTypeDTO = Field(description="Scope type this preset targets.")
    auto_assign: bool = Field(
        description=(
            "Default value for the `auto_assign` flag copied onto roles instantiated "
            "from this preset."
        ),
    )
    deleted: bool = Field(
        description=(
            "Soft-delete flag. Set by the Delete mutation and cleared by the Restore "
            "mutation; archived rows are excluded from default searches."
        ),
    )
    created_at: datetime = Field(description="Creation timestamp.")
    updated_at: datetime = Field(description="Last modification timestamp.")


class CreateRolePresetPayload(BaseResponseModel):
    """Payload for role preset creation."""

    role_preset: RolePresetNode = Field(description="Created role preset.")


class UpdateRolePresetPayload(BaseResponseModel):
    """Payload for role preset update."""

    role_preset: RolePresetNode = Field(description="Updated role preset.")


class BulkRolePresetFailureInfo(BaseResponseModel):
    """Failure detail for a single role preset ID in a bulk role-preset operation."""

    role_preset_id: RolePresetID = Field(
        description="Role preset ID that the operation failed on.",
    )
    message: str = Field(description="Error message describing the failure.")


class BulkDeleteRolePresetsPayload(BaseResponseModel):
    """Payload for bulk-soft-deleting role presets."""

    items: list[RolePresetNode] = Field(
        default_factory=list,
        description="Role presets that were soft-deleted.",
    )
    failed: list[BulkRolePresetFailureInfo] = Field(
        default_factory=list,
        description="Role preset IDs that failed to soft-delete.",
    )


class BulkRestoreRolePresetsPayload(BaseResponseModel):
    """Payload for bulk-restoring soft-deleted role presets."""

    items: list[RolePresetNode] = Field(
        default_factory=list,
        description="Role presets that were restored.",
    )
    failed: list[BulkRolePresetFailureInfo] = Field(
        default_factory=list,
        description="Role preset IDs that failed to restore.",
    )


class BulkPurgeRolePresetsPayload(BaseResponseModel):
    """Payload for bulk-hard-deleting role presets."""

    items: list[RolePresetNode] = Field(
        default_factory=list,
        description="Snapshot of role presets that were purged.",
    )
    failed: list[BulkRolePresetFailureInfo] = Field(
        default_factory=list,
        description="Role preset IDs that failed to purge.",
    )


class SearchRolePresetsPayload(BaseResponseModel):
    """Payload for paginated role preset search results."""

    items: list[RolePresetNode] = Field(description="List of role preset nodes.")
    total_count: int = Field(description="Total number matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")
