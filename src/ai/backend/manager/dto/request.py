import uuid
from typing import Optional

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.storage.registries.types import ModelSortKey, ModelTarget
from ai.backend.manager.data.artifact.modifier import ArtifactModifier
from ai.backend.manager.data.artifact.types import ArtifactType, DelegateeTarget
from ai.backend.manager.defs import ARTIFACT_MAX_SCAN_LIMIT
from ai.backend.manager.types import PaginationOptions, TriState


class DelegateScanArtifactsReq(BaseRequestModel):
    delegator_reservoir_id: Optional[uuid.UUID] = Field(default=None, description="")
    delegatee_target: Optional[DelegateeTarget] = Field(
        default=None,
        description="The unique identifier of the target reservoir to delegate the scan.",
    )
    artifact_type: Optional[ArtifactType] = None
    limit: int = Field(
        lt=ARTIFACT_MAX_SCAN_LIMIT,
        description=f"Maximum number of artifacts to scan (max: {ARTIFACT_MAX_SCAN_LIMIT})",
    )
    order: Optional[ModelSortKey] = None
    search: Optional[str] = None


class ScanArtifactsReq(BaseRequestModel):
    registry_id: Optional[uuid.UUID] = Field(
        default=None, description="The unique identifier of the artifact registry to scan."
    )
    artifact_type: Optional[ArtifactType] = None
    limit: int = Field(
        lt=ARTIFACT_MAX_SCAN_LIMIT,
        description=f"Maximum number of artifacts to scan (max: {ARTIFACT_MAX_SCAN_LIMIT})",
    )
    order: Optional[ModelSortKey] = None
    search: Optional[str] = None


class ScanArtifactsSyncReq(BaseRequestModel):
    registry_id: Optional[uuid.UUID] = Field(
        default=None, description="The unique identifier of the artifact registry to scan."
    )
    artifact_type: Optional[ArtifactType] = None
    limit: int = Field(
        lt=ARTIFACT_MAX_SCAN_LIMIT,
        description=f"Maximum number of artifacts to scan (max: {ARTIFACT_MAX_SCAN_LIMIT})",
    )
    order: Optional[ModelSortKey] = None
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


class ScanArtifactModelPathParam(BaseRequestModel):
    model_id: str = Field(description="The model to scan from the registry.")


class ScanArtifactModelQueryParam(BaseRequestModel):
    revision: Optional[str] = Field(description="The model revision to scan from the registry.")
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


class GetArtifactRevisionReadmeReq(BaseRequestModel):
    artifact_revision_id: uuid.UUID = Field(description="The artifact revision ID to get readme.")


class RejectArtifactRevisionReq(BaseRequestModel):
    artifact_revision_id: uuid.UUID = Field(description="The artifact revision ID to reject.")


class ImportArtifactsReq(BaseRequestModel):
    artifact_revision_ids: list[uuid.UUID] = Field(
        description="List of artifact revision IDs to import."
    )


class UpdateArtifactReqPathParam(BaseRequestModel):
    artifact_id: uuid.UUID = Field(description="The artifact ID to update.")


class UpdateArtifactReqBodyParam(BaseRequestModel):
    readonly: Optional[bool] = Field(
        default=None, description="Whether the artifact should be readonly."
    )
    description: Optional[str] = Field(default=None, description="Updated description")

    def to_modifier(self) -> ArtifactModifier:
        modifier = ArtifactModifier()
        if self.readonly is not None:
            modifier.readonly = TriState.update(self.readonly)
        if self.description is not None:
            modifier.description = TriState.update(self.description)
        return modifier
