"""Request DTOs for Resource Slot API."""

from __future__ import annotations

import uuid

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT

from .types import (
    AgentResourceFilter,
    AgentResourceOrder,
    ResourceAllocationFilter,
    ResourceAllocationOrder,
)

__all__ = (
    "GetAgentResourcesPathParam",
    "SearchAgentResourcesRequest",
    "GetKernelAllocationsPathParam",
    "SearchResourceAllocationsRequest",
)


class GetAgentResourcesPathParam(BaseRequestModel):
    agent_id: str = Field(description="Agent ID")


class SearchAgentResourcesRequest(BaseRequestModel):
    filter: AgentResourceFilter | None = Field(default=None, description="Filter conditions")
    order: list[AgentResourceOrder] | None = Field(default=None, description="Order specification")
    limit: int = Field(
        default=DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT, description="Maximum items to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class GetKernelAllocationsPathParam(BaseRequestModel):
    kernel_id: uuid.UUID = Field(description="Kernel (container) ID")


class SearchResourceAllocationsRequest(BaseRequestModel):
    filter: ResourceAllocationFilter | None = Field(default=None, description="Filter conditions")
    order: list[ResourceAllocationOrder] | None = Field(
        default=None, description="Order specification"
    )
    limit: int = Field(
        default=DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT, description="Maximum items to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
