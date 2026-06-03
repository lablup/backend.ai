"""Request DTOs for role permission preset v2."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import DateTimeFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.rbac.types import (
    OperationTypeFilter,
    RBACElementTypeFilter,
)
from ai.backend.common.dto.manager.v2.role_permission_preset.types import (
    RolePermissionPresetEntry,
    RolePermissionPresetOrderField,
)
from ai.backend.common.identifier.role_permission_preset import RolePermissionPresetID

__all__ = (
    "BulkAddRolePermissionPresetsInput",
    "BulkRemoveRolePermissionPresetsInput",
    "RolePermissionPresetFilter",
    "RolePermissionPresetOrder",
    "SearchRolePermissionPresetsInput",
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


class RolePermissionPresetFilter(BaseRequestModel):
    """Filter criteria for role_permission_presets rows.

    Doubles as the input for the ``permissions`` field resolver under
    ``RolePresetNode``: the resolver supplies ``role_preset_id`` from its parent
    and merges any caller-provided fields here.
    """

    role_preset_id: UUIDFilter | None = Field(
        default=None, description="Filter by parent role preset ID."
    )
    entity_type: RBACElementTypeFilter | None = Field(
        default=None, description="Filter by entity type the permission applies to."
    )
    operation: OperationTypeFilter | None = Field(
        default=None, description="Filter by granted operation."
    )
    created_at: DateTimeFilter | None = Field(
        default=None, description="Filter by creation timestamp."
    )
    AND: list[RolePermissionPresetFilter] | None = Field(
        default=None, description="AND conjunction."
    )
    OR: list[RolePermissionPresetFilter] | None = Field(default=None, description="OR conjunction.")
    NOT: list[RolePermissionPresetFilter] | None = Field(default=None, description="NOT negation.")


RolePermissionPresetFilter.model_rebuild()


class RolePermissionPresetOrder(BaseRequestModel):
    """Order specification for role permission preset search results."""

    field: RolePermissionPresetOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class SearchRolePermissionPresetsInput(BaseRequestModel):
    """Input for paginated search of the permission entries under a role preset."""

    filter: RolePermissionPresetFilter | None = Field(
        default=None, description="Filter conditions."
    )
    order: list[RolePermissionPresetOrder] | None = Field(
        default=None, description="Order specifications."
    )
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")
