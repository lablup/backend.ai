"""Request DTOs for resource slot DTO v2."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.common import BaseFilter

from .types import (
    AgentResourceOrderField,
    AllocatedResourceSlotOrderField,
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
    "ResourceAllocationFilter",
    "ResourceAllocationOrder",
    "ResourceSlotTypeFilter",
    "ResourceSlotTypeOrder",
    "SearchAllocatedResourceSlotsInput",
)


# ========== ResourceSlotType ==========


class ResourceSlotTypeFilter(BaseFilter):
    """Filter conditions for resource slot type search."""

    slot_name: StringFilter | None = Field(default=None, description="Filter by slot name.")
    slot_type: StringFilter | None = Field(default=None, description="Filter by slot type.")
    display_name: StringFilter | None = Field(default=None, description="Filter by display name.")


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


# ========== AgentResource ==========


class AgentResourceFilter(BaseFilter):
    """Filter conditions for agent resource search."""

    slot_name: StringFilter | None = Field(default=None, description="Filter by slot name.")
    agent_id: StringFilter | None = Field(default=None, description="Filter by agent ID.")


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


class ResourceAllocationFilter(BaseFilter):
    """Filter conditions for resource allocation search."""

    slot_name: StringFilter | None = Field(default=None, description="Filter by slot name.")
    kernel_id: UUIDFilter | None = Field(default=None, description="Filter by kernel ID.")


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


class AllocatedResourceSlotFilter(BaseFilter):
    """Filter conditions for allocated resource slot search."""

    slot_name: StringFilter | None = Field(default=None, description="Filter by slot name.")


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
