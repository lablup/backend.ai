"""
Request DTOs for Container Registry domain.

Covers container registry PATCH and Harbor webhook endpoints.

Models already defined in other ``common`` modules are re-exported here
so that callers can import everything from a single domain-specific path.
"""

from ai.backend.common.container_registry import (
    AllowedGroupsModel,
    ContainerRegistryModel,
    PatchContainerRegistryRequestModel,
)
from ai.backend.common.dto.manager.registry.request import HarborWebhookRequestModel

__all__ = (
    # Container registry models (re-exported from common.container_registry)
    "AllowedGroupsModel",
    "ContainerRegistryModel",
    "PatchContainerRegistryRequestModel",
    # Harbor webhook model (re-exported from registry.request)
    "HarborWebhookRequestModel",
)
