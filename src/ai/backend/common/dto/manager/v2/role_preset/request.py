"""Request DTOs for role preset v2."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.role_preset.types import (
    OrderDirection,
    RBACElementTypeDTO,
    RolePermissionPresetEntry,
    RolePresetOrderField,
)
from ai.backend.common.identifier.role_permission_preset import RolePermissionPresetID
from ai.backend.common.identifier.role_preset import RolePresetID

__all__ = (
    "BulkAddRolePermissionPresetsInput",
    "BulkDeleteRolePresetsInput",
    "BulkPurgeRolePresetsInput",
    "BulkRemoveRolePermissionPresetsInput",
    "BulkRestoreRolePresetsInput",
    "CreateRolePresetInput",
    "RolePresetFilter",
    "RolePresetOrder",
    "SearchRolePresetsInput",
    "UpdateRolePresetInput",
)


class CreateRolePresetInput(BaseRequestModel):
    """Input for creating a new role preset."""

    name: str = Field(min_length=1, max_length=64, description="Role preset name.")
    scope_type: RBACElementTypeDTO = Field(
        description="Scope type this preset targets (e.g., domain, project)."
    )
    auto_assign: bool = Field(
        default=False,
        description=(
            "Default value for the `auto_assign` flag on roles instantiated from this "
            "preset. When true, the role is automatically granted to a user upon "
            "joining the scope."
        ),
    )
    permissions: list[RolePermissionPresetEntry] = Field(
        default_factory=list,
        description="Permission entries carried by the preset.",
    )


class UpdateRolePresetInput(BaseRequestModel):
    """Input for updating a role preset's metadata. All fields optional for partial update.

    Permission entries are managed via the dedicated Add/Remove endpoints. The
    ``deleted`` flag is managed through the dedicated Delete/Restore endpoints
    and cannot be mutated here.
    """

    name: str | None = Field(default=None, min_length=1, max_length=64, description="Updated name.")
    auto_assign: bool | None = Field(
        default=None,
        description="Updated default value for the `auto_assign` flag of instantiated roles.",
    )


class BulkDeleteRolePresetsInput(BaseRequestModel):
    """Input for bulk-soft-deleting role presets (sets ``deleted = true``)."""

    role_preset_ids: list[RolePresetID] = Field(
        description="Role preset UUIDs to soft-delete.",
    )


class BulkRestoreRolePresetsInput(BaseRequestModel):
    """Input for bulk-restoring soft-deleted role presets (sets ``deleted = false``)."""

    role_preset_ids: list[RolePresetID] = Field(
        description="Role preset UUIDs to restore.",
    )


class BulkPurgeRolePresetsInput(BaseRequestModel):
    """Input for bulk-hard-deleting role presets. Cascades to their permission entries."""

    role_preset_ids: list[RolePresetID] = Field(
        description="Role preset UUIDs to purge.",
    )


class BulkAddRolePermissionPresetsInput(BaseRequestModel):
    """Input for bulk-adding permission entries to an existing role preset."""

    permissions: list[RolePermissionPresetEntry] = Field(
        description="Permission entries to insert. Duplicates are surfaced as failures.",
    )


class BulkRemoveRolePermissionPresetsInput(BaseRequestModel):
    """Input for bulk-deleting role_permission_presets rows by primary key."""

    permission_preset_ids: list[RolePermissionPresetID] = Field(
        description="role_permission_presets row IDs to delete.",
    )


class RolePresetFilter(BaseRequestModel):
    """Filter criteria for searching role presets."""

    name: StringFilter | None = Field(default=None, description="Filter by name.")
    scope_type: RBACElementTypeDTO | None = Field(default=None, description="Filter by scope type.")
    auto_assign: bool | None = Field(default=None, description="Filter by auto-assign flag.")
    deleted: bool | None = Field(
        default=None,
        description=(
            "Filter by soft-delete flag. Searches exclude soft-deleted rows by default; "
            "set this explicitly to ``true`` to inspect archived presets."
        ),
    )
    AND: list[RolePresetFilter] | None = Field(default=None, description="AND conjunction.")
    OR: list[RolePresetFilter] | None = Field(default=None, description="OR conjunction.")
    NOT: list[RolePresetFilter] | None = Field(default=None, description="NOT negation.")


RolePresetFilter.model_rebuild()


class RolePresetOrder(BaseRequestModel):
    """Order specification for role preset search results."""

    field: RolePresetOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class SearchRolePresetsInput(BaseRequestModel):
    """Input for paginated search of role presets."""

    filter: RolePresetFilter | None = Field(default=None, description="Filter conditions.")
    order: list[RolePresetOrder] | None = Field(default=None, description="Order specifications.")
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")
