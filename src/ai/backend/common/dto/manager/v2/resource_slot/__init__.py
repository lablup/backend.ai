"""
Resource slot DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.resource_slot.request import (
    AdminSearchAgentResourcesInput,
    AdminSearchResourceAllocationsInput,
    AdminSearchResourceSlotTypesInput,
    AgentResourceFilter,
    AgentResourceOrder,
    ResourceAllocationFilter,
    ResourceAllocationOrder,
    ResourceSlotTypeFilter,
    ResourceSlotTypeOrder,
)
from ai.backend.common.dto.manager.v2.resource_slot.response import (
    AdminSearchAgentResourcesPayload,
    AdminSearchResourceAllocationsPayload,
    AdminSearchResourceSlotTypesPayload,
    AgentResourceNode,
    ResourceAllocationNode,
    ResourceSlotTypeNode,
)
from ai.backend.common.dto.manager.v2.resource_slot.types import (
    AgentResourceOrderField,
    NumberFormatInfo,
    OrderDirection,
    ResourceAllocationOrderField,
    ResourceOptsDTOInput,
    ResourceOptsEntryDTO,
    ResourceSlotTypeOrderField,
)

__all__ = (
    # Types
    "AgentResourceOrderField",
    "NumberFormatInfo",
    "OrderDirection",
    "ResourceAllocationOrderField",
    "ResourceOptsEntryDTO",
    "ResourceOptsDTOInput",
    "ResourceSlotTypeOrderField",
    # Request models
    "AdminSearchAgentResourcesInput",
    "AdminSearchResourceAllocationsInput",
    "AdminSearchResourceSlotTypesInput",
    "AgentResourceFilter",
    "AgentResourceOrder",
    "ResourceAllocationFilter",
    "ResourceAllocationOrder",
    "ResourceSlotTypeFilter",
    "ResourceSlotTypeOrder",
    # Response models
    "AdminSearchAgentResourcesPayload",
    "AdminSearchResourceAllocationsPayload",
    "AdminSearchResourceSlotTypesPayload",
    "AgentResourceNode",
    "ResourceAllocationNode",
    "ResourceSlotTypeNode",
)
