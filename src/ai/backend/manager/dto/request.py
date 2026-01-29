import uuid

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.data.storage.registries.types import ModelSortKey, ModelTarget
from ai.backend.manager.data.artifact.types import (
    ArtifactFilterOptions,
    ArtifactOrderingOptions,
    ArtifactType,
    DelegateeTarget,
)
from ai.backend.manager.defs import ARTIFACT_MAX_SCAN_LIMIT
from ai.backend.manager.models.artifact import ArtifactRow
from ai.backend.manager.repositories.artifact.updaters import ArtifactUpdaterSpec
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.types import PaginationOptions, TriState


class DelegateScanArtifactsReq(BaseRequestModel):
    delegator_reservoir_id: uuid.UUID | None = Field(
        default=None, description="ID of the reservoir registry to delegate the scan request to"
    )
    delegatee_target: DelegateeTarget | None = Field(
        default=None,
        description="The unique identifier of the target reservoir to delegate the scan.",
    )
    artifact_type: ArtifactType | None = None
    limit: int = Field(
        lt=ARTIFACT_MAX_SCAN_LIMIT,
        description=f"Maximum number of artifacts to scan (max: {ARTIFACT_MAX_SCAN_LIMIT})",
    )
    order: ModelSortKey | None = None
    search: str | None = None


class ScanArtifactsReq(BaseRequestModel):
    registry_id: uuid.UUID | None = Field(
        default=None, description="The unique identifier of the artifact registry to scan."
    )
    artifact_type: ArtifactType | None = None
    limit: int = Field(
        lt=ARTIFACT_MAX_SCAN_LIMIT,
        description=f"Maximum number of artifacts to scan (max: {ARTIFACT_MAX_SCAN_LIMIT})",
    )
    order: ModelSortKey | None = None
    search: str | None = None


class ScanArtifactsSyncReq(BaseRequestModel):
    registry_id: uuid.UUID | None = Field(
        default=None, description="The unique identifier of the artifact registry to scan."
    )
    artifact_type: ArtifactType | None = None
    limit: int = Field(
        lt=ARTIFACT_MAX_SCAN_LIMIT,
        description=f"Maximum number of artifacts to scan (max: {ARTIFACT_MAX_SCAN_LIMIT})",
    )
    order: ModelSortKey | None = None
    search: str | None = None


class SearchArtifactsReq(BaseRequestModel):
    pagination: PaginationOptions
    ordering: ArtifactOrderingOptions | None = None
    filters: ArtifactFilterOptions | None = None


class ScanArtifactModelsReq(BaseRequestModel):
    models: list[ModelTarget] = Field(description="List of models to scan from the registry.")
    registry_id: uuid.UUID | None = Field(
        default=None, description="The unique identifier of the artifact registry to scan."
    )


class ScanArtifactModelPathParam(BaseRequestModel):
    model_id: str = Field(description="The model to scan from the registry.")


class ScanArtifactModelQueryParam(BaseRequestModel):
    revision: str | None = Field(description="The model revision to scan from the registry.")
    registry_id: uuid.UUID | None = Field(
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


class ImportArtifactsOptions(BaseRequestModel):
    """Options for importing artifact revisions."""

    force: bool = Field(
        default=False, description="Force re-download regardless of digest freshness check."
    )


class DelegateImportArtifactsReq(BaseRequestModel):
    artifact_revision_ids: list[uuid.UUID] = Field(
        description="List of artifact revision IDs to delegate the import request."
    )
    delegator_reservoir_id: uuid.UUID | None = Field(
        default=None, description="ID of the reservoir registry to delegate the import request to"
    )
    delegatee_target: DelegateeTarget | None = Field(
        default=None,
    )
    artifact_type: ArtifactType | None
    options: ImportArtifactsOptions = Field(
        default_factory=ImportArtifactsOptions,
        description="Options controlling import behavior such as forcing re-download.",
    )


class ImportArtifactsReq(BaseRequestModel):
    artifact_revision_ids: list[uuid.UUID] = Field(
        description="List of artifact revision IDs to import."
    )
    vfolder_id: uuid.UUID | None = Field(
        default=None,
        description="Optional vfolder ID to import artifacts directly into.",
    )
    options: ImportArtifactsOptions = Field(
        default_factory=ImportArtifactsOptions,
        description="Options controlling import behavior such as forcing re-download.",
    )


class UpdateArtifactReqPathParam(BaseRequestModel):
    artifact_id: uuid.UUID = Field(description="The artifact ID to update.")


class UpdateArtifactReqBodyParam(BaseRequestModel):
    readonly: bool | None = Field(
        default=None, description="Whether the artifact should be readonly."
    )
    description: str | None = Field(default=None, description="Updated description")

    def to_updater(self, artifact_id: uuid.UUID) -> Updater[ArtifactRow]:
        spec = ArtifactUpdaterSpec()
        if self.readonly is not None:
            spec.readonly = TriState.update(self.readonly)
        if self.description is not None:
            spec.description = TriState.update(self.description)
        return Updater(spec=spec, pk_value=artifact_id)


class GetDownloadProgressReqPathParam(BaseRequestModel):
    artifact_revision_id: uuid.UUID = Field(
        description="The artifact revision ID to get download progress for"
    )
