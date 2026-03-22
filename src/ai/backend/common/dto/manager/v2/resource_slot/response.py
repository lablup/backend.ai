"""
Response DTOs for resource slot DTO v2.
"""

from __future__ import annotations

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.v2.fair_share.types import ResourceSlotInfo

from .types import NumberFormatInfo

__all__ = (
    "ActiveResourceOverviewInfoDTO",
    "AdminSearchAgentResourcesPayload",
    "AdminSearchResourceAllocationsPayload",
    "AdminSearchResourceSlotTypesPayload",
    "AgentResourceNode",
    "ResourceAllocationNode",
    "ResourceSlotTypeNode",
)


class ResourceSlotTypeNode(BaseResponseModel):
    """Node model representing a resource slot type entity."""

    id: str | None = Field(default=None, description="Node ID (same as slot_name).")
    slot_name: str = Field(
        description="Unique identifier for the resource slot (e.g., 'cpu', 'mem', 'cuda.device')."
    )
    slot_type: str = Field(
        description="Category of the slot type (e.g., 'count', 'bytes', 'unique-count')."
    )
    display_name: str = Field(description="Human-readable name for display in UIs.")
    description: str = Field(
        description="Longer description of what this resource slot represents."
    )
    display_unit: str = Field(
        description="Unit label used when displaying resource amounts (e.g., 'GiB', 'cores')."
    )
    display_icon: str = Field(
        description="Icon identifier for UI rendering (e.g., 'cpu', 'memory', 'gpu')."
    )
    number_format: NumberFormatInfo = Field(
        description="Number formatting rules (binary vs decimal prefix, rounding)."
    )
    rank: int = Field(description="Display ordering rank. Lower values appear first.")


class AdminSearchResourceSlotTypesPayload(BaseResponseModel):
    """Payload for admin-scoped paginated resource slot type search results."""

    items: list[ResourceSlotTypeNode] = Field(description="List of resource slot type nodes.")
    total_count: int = Field(description="Total number of resource slot types matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")


class AgentResourceNode(BaseResponseModel):
    """Node model representing a per-agent, per-slot resource capacity and usage entry."""

    id: str = Field(description="Node ID (format: '{agent_id}:{slot_name}').")
    agent_id: str = Field(description="Agent identifier.")
    slot_name: str = Field(
        description="Resource slot identifier (e.g., 'cpu', 'mem', 'cuda.device')."
    )
    capacity: str = Field(
        description="Total hardware resource capacity for this slot on the agent."
    )
    used: str = Field(
        description="Amount of this slot currently consumed by running and scheduled sessions."
    )


class AdminSearchAgentResourcesPayload(BaseResponseModel):
    """Payload for admin-scoped paginated agent resource search results."""

    items: list[AgentResourceNode] = Field(description="List of agent resource nodes.")
    total_count: int = Field(description="Total number of agent resources matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")


class ResourceAllocationNode(BaseResponseModel):
    """Node model representing a per-kernel, per-slot resource allocation entry."""

    id: str = Field(description="Node ID (format: '{kernel_id}:{slot_name}').")
    kernel_id: str = Field(description="Kernel identifier (UUID).")
    slot_name: str = Field(
        description="Resource slot identifier (e.g., 'cpu', 'mem', 'cuda.device')."
    )
    requested: str = Field(
        description="Amount of this resource slot originally requested for the kernel."
    )
    used: str | None = Field(
        default=None,
        description="Amount currently used. May be null if not yet measured.",
    )


class AdminSearchResourceAllocationsPayload(BaseResponseModel):
    """Payload for admin-scoped paginated resource allocation search results."""

    items: list[ResourceAllocationNode] = Field(description="List of resource allocation nodes.")
    total_count: int = Field(
        description="Total number of resource allocations matching the filter."
    )
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")


class ActiveResourceOverviewInfoDTO(BaseResponseModel):
    """Active resource usage overview for a domain or project."""

    slots: ResourceSlotInfo = Field(description="Resource slots currently occupied")
    session_count: int = Field(description="Number of active sessions")
