"""Response DTOs for role preset v2."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.role_preset.types import RBACElementTypeDTO
from ai.backend.common.identifier.role_preset import RolePresetID

__all__ = (
    "AddRolePresetPermissionsPayload",
    "CreateRolePresetPayload",
    "DeleteRolePresetPayload",
    "RemoveRolePresetPermissionsPayload",
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
    auto_apply: bool = Field(description="If true, this preset is auto-applied at scope creation.")
    created_at: datetime = Field(description="Creation timestamp.")
    updated_at: datetime = Field(description="Last modification timestamp.")


class CreateRolePresetPayload(BaseResponseModel):
    """Payload for role preset creation."""

    role_preset: RolePresetNode = Field(description="Created role preset.")


class UpdateRolePresetPayload(BaseResponseModel):
    """Payload for role preset update."""

    role_preset: RolePresetNode = Field(description="Updated role preset.")


class DeleteRolePresetPayload(BaseResponseModel):
    """Payload for role preset deletion."""

    id: RolePresetID = Field(description="UUID of the deleted role preset.")


class AddRolePresetPermissionsPayload(BaseResponseModel):
    """Payload for adding permission entries to a role preset."""

    role_preset: RolePresetNode = Field(description="Role preset metadata.")


class RemoveRolePresetPermissionsPayload(BaseResponseModel):
    """Payload for removing permission entries from a role preset."""

    role_preset: RolePresetNode = Field(description="Role preset metadata.")


class SearchRolePresetsPayload(BaseResponseModel):
    """Payload for paginated role preset search results."""

    items: list[RolePresetNode] = Field(description="List of role preset nodes.")
    total_count: int = Field(description="Total number matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")
