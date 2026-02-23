"""Response DTOs for Resource Slot API."""

from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "PaginationInfo",
    # Agent Resource
    "AgentResourceDTO",
    "GetAgentResourcesResponse",
    "SearchAgentResourcesResponse",
    # Resource Allocation
    "ResourceAllocationDTO",
    "GetKernelAllocationsResponse",
    "SearchResourceAllocationsResponse",
)


class PaginationInfo(BaseModel):
    total: int = Field(description="Total number of items")
    offset: int = Field(description="Number of items skipped")
    limit: int | None = Field(default=None, description="Maximum items returned")


class AgentResourceDTO(BaseModel):
    agent_id: str = Field(description="Agent ID")
    slot_name: str = Field(description="Resource slot name (e.g., cpu, mem, cuda.device)")
    capacity: Decimal = Field(description="Total capacity of this slot on the agent")
    used: Decimal = Field(description="Currently used amount of this slot")


class GetAgentResourcesResponse(BaseResponseModel):
    agent_id: str = Field(description="Agent ID")
    items: list[AgentResourceDTO] = Field(description="Resource slots for the agent")


class SearchAgentResourcesResponse(BaseResponseModel):
    items: list[AgentResourceDTO] = Field(description="Agent resource entries")
    pagination: PaginationInfo = Field(description="Pagination information")


class ResourceAllocationDTO(BaseModel):
    kernel_id: uuid.UUID = Field(description="Kernel (container) ID")
    slot_name: str = Field(description="Resource slot name")
    requested: Decimal = Field(description="Requested amount of this slot")
    used: Decimal | None = Field(
        default=None, description="Actually used amount (None if not yet measured)"
    )


class GetKernelAllocationsResponse(BaseResponseModel):
    kernel_id: uuid.UUID = Field(description="Kernel ID")
    items: list[ResourceAllocationDTO] = Field(description="Resource allocations for the kernel")


class SearchResourceAllocationsResponse(BaseResponseModel):
    items: list[ResourceAllocationDTO] = Field(description="Resource allocation entries")
    pagination: PaginationInfo = Field(description="Pagination information")
