"""Response DTOs for resource preset v2."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.common import BinarySizeInfo, ResourceSlotEntryInfo

__all__ = (
    "AdminSearchResourcePresetsPayload",
    "CreateResourcePresetPayload",
    "DeleteResourcePresetPayload",
    "ResourcePresetNode",
    "UpdateResourcePresetPayload",
)


class ResourcePresetNode(BaseResponseModel):
    """Node model representing a resource preset entity."""

    id: UUID = Field(description="Resource preset UUID.")
    name: str = Field(description="Resource preset name.")
    resource_slots: list[ResourceSlotEntryInfo] = Field(description="Resource slot allocations.")
    shared_memory: BinarySizeInfo | None = Field(
        default=None, description="Shared memory size with both bytes and human-readable format."
    )
    resource_group_name: str | None = Field(
        default=None, description="Resource group name. Null means global preset."
    )


class CreateResourcePresetPayload(BaseResponseModel):
    """Payload for resource preset creation."""

    resource_preset: ResourcePresetNode = Field(description="Created resource preset.")


class UpdateResourcePresetPayload(BaseResponseModel):
    """Payload for resource preset update."""

    resource_preset: ResourcePresetNode = Field(description="Updated resource preset.")


class DeleteResourcePresetPayload(BaseResponseModel):
    """Payload for resource preset deletion."""

    id: UUID = Field(description="UUID of the deleted resource preset.")


class AdminSearchResourcePresetsPayload(BaseResponseModel):
    """Payload for admin-scoped paginated resource preset search results."""

    items: list[ResourcePresetNode] = Field(description="List of resource preset nodes.")
    total_count: int = Field(description="Total number matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")
