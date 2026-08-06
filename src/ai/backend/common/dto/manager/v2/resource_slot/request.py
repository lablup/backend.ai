"""Request DTOs for resource slot DTO v2."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.types import SlotTypes

from .types import (
    AgentResourceOrderField,
    AllocatedResourceSlotOrderField,
    NumberFormatInput,
    OrderDirection,
    ResourceAllocationOrderField,
    ResourceSlotTypeOrderField,
)

__all__ = (
    "AdminSearchAgentResourcesInput",
    "AdminSearchResourceAllocationsInput",
    "AdminSearchResourceSlotTypesInput",
    "AgentResourceFilter",
    "AgentResourceOrder",
    "AllocatedResourceSlotFilter",
    "AllocatedResourceSlotOrder",
    "CreateResourceSlotTypeInput",
    "PurgeResourceSlotTypeInput",
    "ResourceAllocationFilter",
    "ResourceAllocationOrder",
    "ResourceSlotTypeFilter",
    "ResourceSlotTypeOrder",
    "SearchAllocatedResourceSlotsInput",
    "UpdateResourceSlotTypeInput",
)


# ========== ResourceSlotType ==========


class ResourceSlotTypeFilter(BaseRequestModel):
    """Filter conditions for resource slot type search."""

    slot_name: StringFilter | None = Field(default=None, description="Filter by slot name.")
    slot_type: StringFilter | None = Field(default=None, description="Filter by slot type.")
    display_name: StringFilter | None = Field(default=None, description="Filter by display name.")
    AND: list[ResourceSlotTypeFilter] | None = Field(
        default=None, description="Logical AND of multiple filter conditions."
    )
    OR: list[ResourceSlotTypeFilter] | None = Field(
        default=None, description="Logical OR of multiple filter conditions."
    )
    NOT: list[ResourceSlotTypeFilter] | None = Field(
        default=None, description="Logical NOT of filter conditions."
    )


ResourceSlotTypeFilter.model_rebuild()


class ResourceSlotTypeOrder(BaseRequestModel):
    """Order specification for resource slot type search."""

    field: ResourceSlotTypeOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class AdminSearchResourceSlotTypesInput(BaseRequestModel):
    """Input for searching resource slot types with filters, orders, and pagination.

    Supports two pagination modes (mutually exclusive):
    - Cursor-based: first/after (forward) or last/before (backward)
    - Offset-based: limit/offset
    """

    filter: ResourceSlotTypeFilter | None = Field(default=None, description="Filter conditions.")
    order: list[ResourceSlotTypeOrder] | None = Field(
        default=None, description="Order specifications."
    )
    # Cursor-based pagination (Relay)
    first: int | None = Field(default=None, ge=1, description="Number of items from the start.")
    after: str | None = Field(default=None, description="Cursor to paginate forward from.")
    last: int | None = Field(default=None, ge=1, description="Number of items from the end.")
    before: str | None = Field(default=None, description="Cursor to paginate backward from.")
    # Offset-based pagination
    limit: int | None = Field(default=None, ge=1, description="Maximum number of items to return.")
    offset: int | None = Field(default=None, ge=0, description="Number of items to skip.")


class CreateResourceSlotTypeInput(BaseRequestModel):
    """Input for registering a new resource slot type."""

    slot_name: str = Field(
        min_length=1,
        max_length=64,
        description="Unique slot name to register (e.g., 'cpu', 'mem', 'cuda.device').",
    )
    slot_type: SlotTypes = Field(
        description=(
            "Category of the slot type. The scheduler reads this back as a "
            "`SlotTypes` member for every enabled slot, so a value outside the "
            "enum is rejected here rather than breaking the catalog."
        ),
    )
    required: bool = Field(
        default=False,
        description="Whether a session request must name this slot.",
    )
    enabled: bool = Field(
        default=True,
        description="Whether the scheduler considers this slot when placing sessions.",
    )
    display_name: str = Field(default="", max_length=128, description="Human-readable name.")
    description: str = Field(default="", max_length=256, description="Longer description.")
    display_unit: str = Field(default="", max_length=32, description="Unit label (e.g., 'GiB').")
    display_icon: str = Field(default="", max_length=64, description="Icon identifier for UIs.")
    number_format: NumberFormatInput | None = Field(
        default=None, description="Number formatting rules. Defaults to decimal, no rounding."
    )
    rank: int = Field(default=0, description="Display ordering rank. Lower values appear first.")


class UpdateResourceSlotTypeInput(BaseRequestModel):
    """Input for updating a resource slot type.

    ``slot_name`` names the target and is not itself updatable; neither is
    ``slot_type``. Every other field left unset stays unchanged.
    """

    slot_name: str = Field(description="Slot name identifying the slot type to update.")
    required: bool | None = Field(
        default=None, description="Whether a session request must name this slot."
    )
    enabled: bool | None = Field(
        default=None,
        description="Whether the scheduler considers this slot when placing sessions.",
    )
    display_name: str | None = Field(
        default=None, max_length=128, description="Human-readable name."
    )
    description: str | None = Field(default=None, max_length=256, description="Longer description.")
    display_unit: str | None = Field(
        default=None, max_length=32, description="Unit label (e.g., 'GiB')."
    )
    display_icon: str | None = Field(
        default=None, max_length=64, description="Icon identifier for UIs."
    )
    number_format: NumberFormatInput | None = Field(
        default=None, description="Number formatting rules."
    )
    rank: int | None = Field(default=None, description="Display ordering rank.")


class PurgeResourceSlotTypeInput(BaseRequestModel):
    """Input for removing a resource slot type."""

    slot_name: str = Field(description="Slot name identifying the slot type to remove.")


# ========== AgentResource ==========


class AgentResourceFilter(BaseRequestModel):
    """Filter conditions for agent resource search."""

    slot_name: StringFilter | None = Field(default=None, description="Filter by slot name.")
    agent_id: StringFilter | None = Field(default=None, description="Filter by agent ID.")
    AND: list[AgentResourceFilter] | None = Field(
        default=None, description="Logical AND of multiple filter conditions."
    )
    OR: list[AgentResourceFilter] | None = Field(
        default=None, description="Logical OR of multiple filter conditions."
    )
    NOT: list[AgentResourceFilter] | None = Field(
        default=None, description="Logical NOT of filter conditions."
    )


AgentResourceFilter.model_rebuild()


class AgentResourceOrder(BaseRequestModel):
    """Order specification for agent resource search."""

    field: AgentResourceOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class AdminSearchAgentResourcesInput(BaseRequestModel):
    """Input for searching agent resources with filters, orders, and pagination.

    Supports two pagination modes (mutually exclusive):
    - Cursor-based: first/after (forward) or last/before (backward)
    - Offset-based: limit/offset
    """

    filter: AgentResourceFilter | None = Field(default=None, description="Filter conditions.")
    order: list[AgentResourceOrder] | None = Field(
        default=None, description="Order specifications."
    )
    # Cursor-based pagination (Relay)
    first: int | None = Field(default=None, ge=1, description="Number of items from the start.")
    after: str | None = Field(default=None, description="Cursor to paginate forward from.")
    last: int | None = Field(default=None, ge=1, description="Number of items from the end.")
    before: str | None = Field(default=None, description="Cursor to paginate backward from.")
    # Offset-based pagination
    limit: int | None = Field(default=None, ge=1, description="Maximum number of items to return.")
    offset: int | None = Field(default=None, ge=0, description="Number of items to skip.")


# ========== ResourceAllocation ==========


class ResourceAllocationFilter(BaseRequestModel):
    """Filter conditions for resource allocation search."""

    slot_name: StringFilter | None = Field(default=None, description="Filter by slot name.")
    kernel_id: UUIDFilter | None = Field(default=None, description="Filter by kernel ID.")
    AND: list[ResourceAllocationFilter] | None = Field(
        default=None, description="Logical AND of multiple filter conditions."
    )
    OR: list[ResourceAllocationFilter] | None = Field(
        default=None, description="Logical OR of multiple filter conditions."
    )
    NOT: list[ResourceAllocationFilter] | None = Field(
        default=None, description="Logical NOT of filter conditions."
    )


ResourceAllocationFilter.model_rebuild()


class ResourceAllocationOrder(BaseRequestModel):
    """Order specification for resource allocation search."""

    field: ResourceAllocationOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class AdminSearchResourceAllocationsInput(BaseRequestModel):
    """Input for searching resource allocations with filters, orders, and pagination."""

    filter: ResourceAllocationFilter | None = Field(default=None, description="Filter conditions.")
    order: list[ResourceAllocationOrder] | None = Field(
        default=None, description="Order specifications."
    )
    first: int | None = Field(default=None, ge=1, description="Number of items from the start.")
    after: str | None = Field(default=None, description="Cursor to paginate forward from.")
    last: int | None = Field(default=None, ge=1, description="Number of items from the end.")
    before: str | None = Field(default=None, description="Cursor to paginate backward from.")
    limit: int | None = Field(default=None, ge=1, description="Maximum number of items to return.")
    offset: int | None = Field(default=None, ge=0, description="Number of items to skip.")


# ========== AllocatedResourceSlot (revision/preset shared) ==========


class AllocatedResourceSlotFilter(BaseRequestModel):
    """Filter conditions for allocated resource slot search."""

    slot_name: StringFilter | None = Field(default=None, description="Filter by slot name.")
    AND: list[AllocatedResourceSlotFilter] | None = Field(
        default=None, description="Logical AND of multiple filter conditions."
    )
    OR: list[AllocatedResourceSlotFilter] | None = Field(
        default=None, description="Logical OR of multiple filter conditions."
    )
    NOT: list[AllocatedResourceSlotFilter] | None = Field(
        default=None, description="Logical NOT of filter conditions."
    )


AllocatedResourceSlotFilter.model_rebuild()


class AllocatedResourceSlotOrder(BaseRequestModel):
    """Order specification for allocated resource slot search."""

    field: AllocatedResourceSlotOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class SearchAllocatedResourceSlotsInput(BaseRequestModel):
    """Input for searching allocated resource slots with filters, orders, and pagination.

    Shared by both deployment revision and preset resource slot connections.
    """

    filter: AllocatedResourceSlotFilter | None = Field(
        default=None, description="Filter conditions."
    )
    order: list[AllocatedResourceSlotOrder] | None = Field(
        default=None, description="Order specifications."
    )
    first: int | None = Field(default=None, ge=1, description="Number of items from the start.")
    after: str | None = Field(default=None, description="Cursor to paginate forward from.")
    last: int | None = Field(default=None, ge=1, description="Number of items from the end.")
    before: str | None = Field(default=None, description="Cursor to paginate backward from.")
    limit: int | None = Field(default=None, ge=1, description="Maximum number of items to return.")
    offset: int | None = Field(default=None, ge=0, description="Number of items to skip.")
