"""
Container Registry DTOs v2 for Manager API.
"""

from ai.backend.common.dto.manager.v2.container_registry.request import (
    AllowedGroupsInput,
    CreateContainerRegistryInput,
    DeleteContainerRegistryInput,
    UpdateContainerRegistryInput,
)
from ai.backend.common.dto.manager.v2.container_registry.response import (
    ContainerRegistryNode,
    CreateContainerRegistryPayload,
    DeleteContainerRegistryPayload,
    ListContainerRegistriesPayload,
    UpdateContainerRegistryPayload,
)
from ai.backend.common.dto.manager.v2.container_registry.types import ContainerRegistryType

__all__ = (
    # Types
    "ContainerRegistryType",
    # Input models (request)
    "AllowedGroupsInput",
    "CreateContainerRegistryInput",
    "DeleteContainerRegistryInput",
    "UpdateContainerRegistryInput",
    # Node and Payload models (response)
    "ContainerRegistryNode",
    "CreateContainerRegistryPayload",
    "DeleteContainerRegistryPayload",
    "ListContainerRegistriesPayload",
    "UpdateContainerRegistryPayload",
)
