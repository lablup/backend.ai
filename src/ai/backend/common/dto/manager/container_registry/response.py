"""
Response DTOs for Container Registry domain.

Models already defined in other ``common`` modules are re-exported here
so that callers can import everything from a single domain-specific path.
"""

from ai.backend.common.container_registry import (
    ContainerRegistryModel,
    PatchContainerRegistryResponseModel,
)

__all__ = (
    # Container registry models (re-exported from common.container_registry)
    "ContainerRegistryModel",
    "PatchContainerRegistryResponseModel",
)
