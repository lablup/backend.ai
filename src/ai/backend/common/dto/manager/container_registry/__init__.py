"""
Container Registry DTOs for Manager API.

Covers container registry PATCH and Harbor webhook endpoints.

Import directly from submodules:
- request: PatchContainerRegistryRequestModel, HarborWebhookRequestModel, etc.
- response: PatchContainerRegistryResponseModel, etc.
- types: ContainerRegistryType
"""

from .request import (
    AllowedGroupsModel,
    ContainerRegistryModel,
    HarborWebhookRequestModel,
    PatchContainerRegistryRequestModel,
)
from .response import (
    PatchContainerRegistryResponseModel,
)
from .types import (
    ContainerRegistryType,
)

__all__ = (
    # Types
    "ContainerRegistryType",
    # Request DTOs
    "AllowedGroupsModel",
    "ContainerRegistryModel",
    "PatchContainerRegistryRequestModel",
    "HarborWebhookRequestModel",
    # Response DTOs
    "PatchContainerRegistryResponseModel",
)
