"""Resource Slot DTOs package."""

from __future__ import annotations

from .request import (
    GetAgentResourcesPathParam,
    GetKernelAllocationsPathParam,
    SearchAgentResourcesRequest,
    SearchResourceAllocationsRequest,
)
from .response import (
    AgentResourceDTO,
    GetAgentResourcesResponse,
    GetKernelAllocationsResponse,
    PaginationInfo,
    ResourceAllocationDTO,
    SearchAgentResourcesResponse,
    SearchResourceAllocationsResponse,
)
from .types import (
    AgentResourceFilter,
    AgentResourceOrder,
    AgentResourceOrderField,
    OrderDirection,
    ResourceAllocationFilter,
    ResourceAllocationOrder,
    ResourceAllocationOrderField,
)

__all__ = (
    # Types
    "OrderDirection",
    "AgentResourceOrderField",
    "AgentResourceFilter",
    "AgentResourceOrder",
    "ResourceAllocationOrderField",
    "ResourceAllocationFilter",
    "ResourceAllocationOrder",
    # Request
    "GetAgentResourcesPathParam",
    "SearchAgentResourcesRequest",
    "GetKernelAllocationsPathParam",
    "SearchResourceAllocationsRequest",
    # Response
    "PaginationInfo",
    "AgentResourceDTO",
    "GetAgentResourcesResponse",
    "SearchAgentResourcesResponse",
    "ResourceAllocationDTO",
    "GetKernelAllocationsResponse",
    "SearchResourceAllocationsResponse",
)
