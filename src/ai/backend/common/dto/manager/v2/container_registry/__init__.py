"""
Container Registry DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.container_registry.request import (
    AdminSearchContainerRegistriesInput,
    AllowedGroupsInput,
    ContainerRegistryFilter,
    ContainerRegistryOrder,
    CreateContainerRegistryInput,
    DeleteContainerRegistryInput,
    UpdateContainerRegistryInput,
)
from ai.backend.common.dto.manager.v2.container_registry.response import (
    AdminSearchContainerRegistriesPayload,
    ContainerRegistryNode,
    CreateContainerRegistryPayload,
    DeleteContainerRegistryPayload,
    UpdateContainerRegistryPayload,
)
from ai.backend.common.dto.manager.v2.container_registry.types import (
    ContainerRegistryOrderField,
    ContainerRegistryType,
    ContainerRegistryTypeFilter,
    OrderDirection,
)

__all__ = (
    # Types
    "ContainerRegistryOrderField",
    "ContainerRegistryType",
    "ContainerRegistryTypeFilter",
    "OrderDirection",
    # Input models (request)
    "AllowedGroupsInput",
    "ContainerRegistryFilter",
    "ContainerRegistryOrder",
    "CreateContainerRegistryInput",
    "DeleteContainerRegistryInput",
    "AdminSearchContainerRegistriesInput",
    "UpdateContainerRegistryInput",
    # Node and Payload models (response)
    "ContainerRegistryNode",
    "CreateContainerRegistryPayload",
    "DeleteContainerRegistryPayload",
    "AdminSearchContainerRegistriesPayload",
    "UpdateContainerRegistryPayload",
)
