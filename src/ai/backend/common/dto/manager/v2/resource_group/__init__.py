"""
Resource group DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.resource_group.request import (
    AdminSearchResourceGroupsInput,
    CreateResourceGroupInput,
    DeleteResourceGroupInput,
    PreemptionConfigInputDTO,
    ResourceGroupFilter,
    ResourceGroupOrder,
    ResourceWeightEntryInput,
    UpdateResourceGroupConfigInput,
    UpdateResourceGroupFairShareSpecInput,
    UpdateResourceGroupInput,
)
from ai.backend.common.dto.manager.v2.resource_group.response import (
    AdminSearchResourceGroupsPayload,
    CreateResourceGroupPayload,
    DeleteResourceGroupPayload,
    ResourceGroupNode,
    UpdateResourceGroupPayload,
)
from ai.backend.common.dto.manager.v2.resource_group.types import (
    OrderDirection,
    ResourceGroupOrderDirection,
    ResourceGroupOrderField,
)

__all__ = (
    # Types
    "OrderDirection",
    "ResourceGroupOrderDirection",
    "ResourceGroupOrderField",
    # Input models (request)
    "AdminSearchResourceGroupsInput",
    "CreateResourceGroupInput",
    "DeleteResourceGroupInput",
    "PreemptionConfigInputDTO",
    "ResourceGroupFilter",
    "ResourceGroupOrder",
    "ResourceWeightEntryInput",
    "UpdateResourceGroupConfigInput",
    "UpdateResourceGroupFairShareSpecInput",
    "UpdateResourceGroupInput",
    # Node and Payload models (response)
    "AdminSearchResourceGroupsPayload",
    "CreateResourceGroupPayload",
    "DeleteResourceGroupPayload",
    "ResourceGroupNode",
    "UpdateResourceGroupPayload",
)
