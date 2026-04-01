"""
Response DTOs for registry domain.

Covers container registry, artifact registry (common-safe subset),
and group registry quota endpoints.

Models already defined in other ``common`` modules are re-exported here
so that callers can import everything from a single domain-specific path.

Note: Artifact registry response models that depend on manager-specific types
(e.g., ArtifactData, ArtifactRevisionResponseData) remain in
``ai.backend.manager.dto.response`` to comply with the ``common → manager``
visibility constraint.
"""

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.container_registry import (
    ContainerRegistryModel,
    PatchContainerRegistryResponseModel,
)
from ai.backend.common.dto.manager.response import (
    DeleteArtifactResponse,
    ImportArtifactResponse,
    UpdateArtifactResponse,
)

__all__ = (
    # Container registry models (re-exported from common.container_registry)
    "ContainerRegistryModel",
    "PatchContainerRegistryResponseModel",
    # Artifact registry models (re-exported from common.dto.manager.response)
    "ImportArtifactResponse",
    "UpdateArtifactResponse",
    "DeleteArtifactResponse",
    # Group registry quota models (NEW)
    "RegistryQuotaResponse",
)


# ---------------------------------------------------------------------------
# Group registry quota models (NEW)
# ---------------------------------------------------------------------------


class RegistryQuotaResponse(BaseResponseModel):
    """Response for registry quota operations."""

    result: int | None = Field(
        default=None, description="The current registry quota value for the group."
    )
