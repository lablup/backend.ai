"""
Request DTOs for registry domain.

Covers container registry, HuggingFace registry,
and group registry quota endpoints.

Note: Artifact registry request models that depend on manager-specific types
(e.g., ArtifactType, DelegateeTarget, PaginationOptions) remain in
``ai.backend.manager.dto.request`` to comply with the ``common → manager``
visibility constraint.
"""

import uuid
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from ai.backend.common.api_handlers import BaseFieldModel, BaseRequestModel
from ai.backend.common.container_registry import ContainerRegistryType

__all__ = (
    # Container registry models
    "AllowedGroupsModel",
    "ContainerRegistryModel",
    "PatchContainerRegistryRequestModel",
    "HarborWebhookRequestModel",
    # HuggingFace registry models
    "CreateHuggingFaceRegistryReq",
    "DeleteHuggingFaceRegistryReq",
    # Artifact registry models (common-safe subset)
    "ImportArtifactPathParam",
    "ImportArtifactReq",
    "UpdateArtifactPathParam",
    "UpdateArtifactReq",
    "DeleteArtifactPathParam",
    # Group registry quota models (NEW)
    "CreateRegistryQuotaReq",
    "ReadRegistryQuotaReq",
    "UpdateRegistryQuotaReq",
    "DeleteRegistryQuotaReq",
)


# ---------------------------------------------------------------------------
# Container registry models (from common/container_registry.py)
# ---------------------------------------------------------------------------


class AllowedGroupsModel(BaseFieldModel):
    add: list[str] = []
    remove: list[str] = []


class ContainerRegistryModel(BaseModel):
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


class PatchContainerRegistryRequestModel(ContainerRegistryModel, BaseRequestModel):
    allowed_groups: AllowedGroupsModel | None = None


# ---------------------------------------------------------------------------
# Harbor webhook model (from manager/api/container_registry.py)
# ---------------------------------------------------------------------------


class HarborWebhookRequestModel(BaseRequestModel):
    type: str = Field(
        description="Type of the webhook event triggered by Harbor. See Harbor documentation for details."
    )

    class EventData(BaseFieldModel):
        class Resource(BaseFieldModel):
            resource_url: str = Field(description="URL of the artifact")
            tag: str = Field(description="Tag of the artifact")

        class Repository(BaseFieldModel):
            namespace: str = Field(description="Harbor project (namespace)")
            name: str = Field(description="Name of the repository")

        resources: list[Resource] = Field(
            description="List of related artifacts involved in the event"
        )
        repository: Repository = Field(description="Repository details")

    event_data: EventData = Field(description="Event details")


# ---------------------------------------------------------------------------
# HuggingFace registry models (from common/dto/manager/request.py)
# ---------------------------------------------------------------------------


class CreateHuggingFaceRegistryReq(BaseRequestModel):
    name: str = Field(description="Name of the Hugging Face model registry")
    endpoint: str = Field(
        description="Endpoint URL of the Hugging Face model registry",
        examples=["https://huggingface.co"],
    )
    token: str | None = Field(
        description="Authentication token for the Hugging Face model registry",
        examples=["your_token_here"],
    )


class DeleteHuggingFaceRegistryReq(BaseRequestModel):
    id: uuid.UUID = Field(description="The unique identifier of the Hugging Face model registry")


# ---------------------------------------------------------------------------
# Artifact registry models — common-safe subset
# (from common/dto/manager/request.py; no manager dependencies)
# ---------------------------------------------------------------------------


class ImportArtifactPathParam(BaseRequestModel):
    artifact_id: uuid.UUID = Field(
        description="The unique identifier of the artifact to be imported."
    )


class ImportArtifactReq(BaseRequestModel):
    storage_id: uuid.UUID = Field(
        description="The unique identifier of the storage where the artifact will be imported."
    )


class UpdateArtifactPathParam(BaseRequestModel):
    artifact_id: uuid.UUID = Field(
        description="The unique identifier of the artifact to be updated."
    )


class UpdateArtifactReq(BaseRequestModel):
    description: str | None = Field(default=None, description="Updated description")
    readonly: bool | None = Field(
        default=None, description="Whether the artifact should be readonly."
    )


class DeleteArtifactPathParam(BaseRequestModel):
    artifact_id: uuid.UUID = Field(
        description="The unique identifier of the artifact to be deleted."
    )


# ---------------------------------------------------------------------------
# Group registry quota models (NEW)
# ---------------------------------------------------------------------------


class CreateRegistryQuotaReq(BaseRequestModel):
    """Request to create a registry quota for a group."""

    group_id: str = Field(
        description="The group (project) ID to create the registry quota for.",
        validation_alias=AliasChoices("group_id", "group"),
    )
    quota: int = Field(description="The registry quota value to set.")


class ReadRegistryQuotaReq(BaseRequestModel):
    """Request to read a registry quota for a group."""

    group_id: str = Field(
        description="The group (project) ID to read the registry quota for.",
        validation_alias=AliasChoices("group_id", "group"),
    )


class UpdateRegistryQuotaReq(BaseRequestModel):
    """Request to update a registry quota for a group."""

    group_id: str = Field(
        description="The group (project) ID to update the registry quota for.",
        validation_alias=AliasChoices("group_id", "group"),
    )
    quota: int = Field(description="The new registry quota value.")


class DeleteRegistryQuotaReq(BaseRequestModel):
    """Request to delete a registry quota for a group."""

    group_id: str = Field(
        description="The group (project) ID to delete the registry quota for.",
        validation_alias=AliasChoices("group_id", "group"),
    )
