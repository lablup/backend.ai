"""Request DTOs for resource slot DTO v2."""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter

from .types import (
    AgentResourceOrderField,
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
    "ResourceAllocationFilter",
    "ResourceAllocationOrder",
    "ResourceSlotTypeFilter",
    "ResourceSlotTypeOrder",
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
    """Input for searching resource allocations with filters, orders, and pagination.

    Supports two pagination modes (mutually exclusive):
    - Cursor-based: first/after (forward) or last/before (backward)
    - Offset-based: limit/offset
    """

    filter: ResourceAllocationFilter | None = Field(default=None, description="Filter conditions.")
    order: list[ResourceAllocationOrder] | None = Field(
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
