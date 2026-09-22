"""Request DTOs for resource preset v2."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.common import BinarySizeInput, ResourceSlotEntryInput
from ai.backend.common.dto.manager.v2.resource_preset.types import (
    ResourcePresetOrderDirection,
    ResourcePresetOrderField,
)
from ai.backend.common.tristate.unset import UNSET, Unset

__all__ = (
    "AdminSearchResourcePresetsInput",
    "CreateResourcePresetInput",
    "ResourcePresetFilter",
    "ResourcePresetOrder",
    "UpdateResourcePresetInput",
)


class CreateResourcePresetInput(BaseRequestModel):
    """Input for creating a new resource preset."""

    name: str = Field(min_length=1, max_length=256, description="Resource preset name.")
    resource_slots: list[ResourceSlotEntryInput] = Field(
        description="Resource slot allocations for this preset."
    )
    shared_memory: BinarySizeInput | None = Field(
        default=None,
        description="Shared memory size. Provide value (bytes) or display (e.g., '1g').",
    )
    resource_group_name: str | None = Field(
        default=None,
        description="Resource group name. If null, the preset is global.",
    )


class UpdateResourcePresetInput(BaseRequestModel):
    """Input for updating a resource preset. All fields optional for partial update."""

    id: UUID = Field(description="UUID of the resource preset to update.")
    name: str | None | Unset = Field(
        default=UNSET, description="Updated name. Omit to leave unchanged."
    )
    resource_slots: list[ResourceSlotEntryInput] | None | Unset = Field(
        default=UNSET, description="Updated resource slot allocations. Omit to leave unchanged."
    )
    shared_memory: BinarySizeInput | None | Unset = Field(
        default=UNSET,
        description="Updated shared memory. Omit to leave unchanged; null clears.",
    )
    resource_group_name: str | None | Unset = Field(
        default=UNSET,
        description="Updated resource group name. Omit to leave unchanged; null makes the preset global.",
    )


class ResourcePresetFilter(BaseRequestModel):
    """Filter criteria for searching resource presets."""

    name: StringFilter | None = Field(default=None, description="Filter by name.")
    resource_group_name: StringFilter | None = Field(
        default=None, description="Filter by resource group name."
    )
    AND: list[ResourcePresetFilter] | None = Field(default=None, description="AND conjunction.")
    OR: list[ResourcePresetFilter] | None = Field(default=None, description="OR conjunction.")
    NOT: list[ResourcePresetFilter] | None = Field(default=None, description="NOT negation.")


ResourcePresetFilter.model_rebuild()


class ResourcePresetOrder(BaseRequestModel):
    """Order specification for resource preset search results."""

    field: ResourcePresetOrderField = Field(description="Field to order by.")
    direction: ResourcePresetOrderDirection = Field(
        default=ResourcePresetOrderDirection.ASC, description="Order direction."
    )


class AdminSearchResourcePresetsInput(BaseRequestModel):
    """Input for admin search of resource presets with pagination."""

    filter: ResourcePresetFilter | None = Field(default=None, description="Filter conditions.")
    order: list[ResourcePresetOrder] | None = Field(
        default=None, description="Order specifications."
    )
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")
