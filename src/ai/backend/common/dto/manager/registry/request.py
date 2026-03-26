"""
Request DTOs for registry domain.

Covers container registry, HuggingFace registry,
and group registry quota endpoints.

Models already defined in other ``common`` modules are re-exported here
so that callers can import everything from a single domain-specific path.

Note: Artifact registry request models that depend on manager-specific types
(e.g., ArtifactType, DelegateeTarget, PaginationOptions) remain in
``ai.backend.manager.dto.request`` to comply with the ``common → manager``
visibility constraint.
"""

from pydantic import AliasChoices, Field

from ai.backend.common.api_handlers import BaseFieldModel, BaseRequestModel
from ai.backend.common.container_registry import (
    AllowedGroupsModel,
    ContainerRegistryModel,
    PatchContainerRegistryRequestModel,
)
from ai.backend.common.dto.manager.request import (
    CreateHuggingFaceRegistryReq,
    DeleteArtifactPathParam,
    DeleteHuggingFaceRegistryReq,
    ImportArtifactPathParam,
    ImportArtifactReq,
    UpdateArtifactPathParam,
    UpdateArtifactReq,
)

__all__ = (
    # Container registry models (re-exported from common.container_registry)
    "AllowedGroupsModel",
    "ContainerRegistryModel",
    "PatchContainerRegistryRequestModel",
    "HarborWebhookRequestModel",
    # HuggingFace registry models (re-exported from common.dto.manager.request)
    "CreateHuggingFaceRegistryReq",
    "DeleteHuggingFaceRegistryReq",
    # Artifact registry models (re-exported from common.dto.manager.request)
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
# Harbor webhook model (unique to this module)
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
