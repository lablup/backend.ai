import uuid
from typing import Optional

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.storage.registries.types import ModelTarget
from ai.backend.manager.data.artifact.modifier import ArtifactModifier
from ai.backend.manager.data.artifact.types import ArtifactType
from ai.backend.manager.types import PaginationOptions


class ScanArtifactsReq(BaseRequestModel):
    registry_id: Optional[uuid.UUID] = Field(
        default=None, description="The unique identifier of the artifact registry to scan."
    )
    artifact_type: Optional[ArtifactType] = None
    limit: int
    search: Optional[str] = None


class SearchArtifactsReq(BaseRequestModel):
    pagination: PaginationOptions
    # TODO: Support this. (we need to make strawberry independent types)
    # ordering: Optional[ArtifactOrderingOptions] = None
    # filters: Optional[ArtifactFilterOptions] = None


class ScanArtifactModelsReq(BaseRequestModel):
    models: list[ModelTarget] = Field(description="List of models to scan from the registry.")
    registry_id: Optional[uuid.UUID] = Field(
        default=None, description="The unique identifier of the artifact registry to scan."
    )


class CleanupArtifactsReq(BaseRequestModel):
    artifact_revision_ids: list[uuid.UUID] = Field(
        description="List of artifact revision IDs to cleanup."
    )


class CancelImportArtifactReq(BaseRequestModel):
    artifact_revision_id: uuid.UUID = Field(
        description="The artifact revision ID to cancel import."
    )


class ApproveArtifactRevisionReq(BaseRequestModel):
    artifact_revision_id: uuid.UUID = Field(description="The artifact revision ID to approve.")


class RejectArtifactRevisionReq(BaseRequestModel):
    artifact_revision_id: uuid.UUID = Field(description="The artifact revision ID to reject.")


class ImportArtifactsReq(BaseRequestModel):
    artifact_revision_ids: list[uuid.UUID] = Field(
        description="List of artifact revision IDs to import."
    )


class UpdateArtifactReq(BaseRequestModel):
    artifact_id: uuid.UUID = Field(description="The artifact ID to update.")
    modifier: ArtifactModifier = Field(description="Fields to modify in the artifact.")
