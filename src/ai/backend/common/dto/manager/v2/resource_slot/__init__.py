"""
Resource slot DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AdminSearchAgentResourcesInput,
    AdminSearchResourceAllocationsInput,
    AdminSearchResourceSlotTypesInput,
    AgentResourceFilter,
    AgentResourceOrder,
    AllocatedResourceSlotFilter,
    AllocatedResourceSlotOrder,
    ResourceAllocationFilter,
    ResourceAllocationOrder,
    ResourceSlotTypeFilter,
    ResourceSlotTypeOrder,
    SearchAllocatedResourceSlotsInput,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    ActiveResourceOverviewInfoDTO,
    AdminSearchAgentResourcesPayload,
    AdminSearchResourceAllocationsPayload,
    AdminSearchResourceSlotTypesPayload,
    AgentResourceNode,
    AllocatedResourceSlotNode,
    ResourceAllocationNode,
    ResourceSlotTypeNode,
    SearchAllocatedResourceSlotsPayload,
)
from ai.backend.common.dto.manager.v2.resource_slot.types import (
    AgentResourceOrderField,
    AllocatedResourceSlotOrderField,
    NumberFormatInfo,
    OrderDirection,
    ResourceAllocationOrderField,
    ResourceOptsDTOInput,
    ResourceOptsEntryDTO,
    ResourceSlotTypeOrderField,
    ServicePortEntryInfoDTO,
    ServicePortsInfoDTO,
)

__all__ = (
    # Types
    "AgentResourceOrderField",
    "AllocatedResourceSlotOrderField",
    "NumberFormatInfo",
    "OrderDirection",
    "ResourceAllocationOrderField",
    "ResourceOptsEntryDTO",
    "ResourceOptsDTOInput",
    "ResourceSlotTypeOrderField",
    "ServicePortEntryInfoDTO",
    "ServicePortsInfoDTO",
    # Request models
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
    # Response models
    "ActiveResourceOverviewInfoDTO",
    "AdminSearchAgentResourcesPayload",
    "AdminSearchResourceAllocationsPayload",
    "AdminSearchResourceSlotTypesPayload",
    "AgentResourceNode",
    "AllocatedResourceSlotNode",
    "ResourceAllocationNode",
    "ResourceSlotTypeNode",
    "SearchAllocatedResourceSlotsPayload",
)
