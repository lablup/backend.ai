"""
Response DTOs for registry domain.

Covers container registry, artifact registry (common-safe subset),
and group registry quota endpoints.

Note: Artifact registry response models that depend on manager-specific types
(e.g., ArtifactData, ArtifactRevisionResponseData) remain in
``ai.backend.manager.dto.response`` to comply with the ``common → manager``
visibility constraint.
"""

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.container_registry import ContainerRegistryType

__all__ = (
    # Container registry models
    "PatchContainerRegistryResponseModel",
    # Artifact registry models (common-safe subset)
    "ImportArtifactResponse",
    "UpdateArtifactResponse",
    "DeleteArtifactResponse",
    # Group registry quota models (NEW)
    "RegistryQuotaResponse",
)


# ---------------------------------------------------------------------------
# Container registry models (from common/container_registry.py)
# ---------------------------------------------------------------------------


class ContainerRegistryResponseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | None = None
    url: str | None = None
    registry_name: str | None = None
    type: ContainerRegistryType | None = None
    project: str | None = None
    username: str | None = None
    password: str | None = None
    ssl_verify: bool | None = None
    is_global: bool | None = None
    extra: dict[str, Any] | None = None


class PatchContainerRegistryResponseModel(ContainerRegistryResponseModel, BaseResponseModel):
    pass


# ---------------------------------------------------------------------------
# Artifact registry models — common-safe subset
# (from common/dto/manager/response.py; no manager dependencies)
# ---------------------------------------------------------------------------


class ImportArtifactResponse(BaseResponseModel):
    artifact_id: str = Field(description="ID of the imported artifact")
    name: str = Field(description="Name of the artifact")
    version: str = Field(description="Version of the artifact")
    size: int = Field(description="Size of the artifact in bytes")


class UpdateArtifactResponse(BaseResponseModel):
    artifact_id: str = Field(description="ID of the updated artifact")
    name: str = Field(description="Name of the artifact")
    version: str = Field(description="Version of the artifact")


class DeleteArtifactResponse(BaseResponseModel):
    artifact_id: str = Field(description="ID of the deleted artifact")
    message: str = Field(description="Deletion confirmation message")


# ---------------------------------------------------------------------------
# Group registry quota models (NEW)
# ---------------------------------------------------------------------------


class RegistryQuotaResponse(BaseResponseModel):
    """Response for registry quota operations."""

    result: int | None = Field(
        default=None, description="The current registry quota value for the group."
    )
