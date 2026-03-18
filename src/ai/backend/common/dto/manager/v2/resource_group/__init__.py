"""
Resource group DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.resource_group.request import (
    CreateResourceGroupInput,
    DeleteResourceGroupInput,
    UpdateResourceGroupInput,
)
from ai.backend.common.dto.manager.v2.resource_group.response import (
    CreateResourceGroupPayload,
    DeleteResourceGroupPayload,
    ResourceGroupNode,
    UpdateResourceGroupPayload,
)
from ai.backend.common.dto.manager.v2.resource_group.types import (
    OrderDirection,
    ResourceGroupOrderField,
)

__all__ = (
    # Types
    "OrderDirection",
    "ResourceGroupOrderField",
    # Input models (request)
    "CreateResourceGroupInput",
    "DeleteResourceGroupInput",
    "UpdateResourceGroupInput",
    # Node and Payload models (response)
    "CreateResourceGroupPayload",
    "DeleteResourceGroupPayload",
    "ResourceGroupNode",
    "UpdateResourceGroupPayload",
)
