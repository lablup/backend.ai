import uuid
from typing import Optional

from pydantic import BaseModel

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.manager.data.artifact.types import (
    ArtifactData,
    ArtifactDataWithRevisions,
    ArtifactDataWithRevisionsResponse,
    ArtifactRevisionReadme,
    ArtifactRevisionResponseData,
)


class HealthResponse(BaseModel):
    """Standard health check response"""

    status: str
    version: str
    component: str


class SearchArtifactsResponse(BaseResponseModel):
    artifacts: list[ArtifactDataWithRevisionsResponse]


class ScanArtifactsResponse(BaseResponseModel):
    artifacts: list[ArtifactDataWithRevisionsResponse]


class ScanArtifactsSyncResponse(BaseResponseModel):
    artifacts: list[ArtifactDataWithRevisionsResponse]
    readme_data: dict[uuid.UUID, ArtifactRevisionReadme]


class DelegateScanArtifactsResponse(BaseResponseModel):
    artifacts: list[ArtifactDataWithRevisionsResponse]
    source_registry_id: uuid.UUID
    source_registry_type: ArtifactRegistryType
    readme_data: dict[uuid.UUID, ArtifactRevisionReadme]


class ScanArtifactModelsResponse(BaseResponseModel):
    artifacts: list[ArtifactDataWithRevisionsResponse]


class RetreiveArtifactModelsResponse(BaseResponseModel):
    artifacts: list[ArtifactDataWithRevisionsResponse]


class RetreiveArtifactModelResponse(BaseResponseModel):
    artifact: ArtifactDataWithRevisions


class CleanupArtifactsResponse(BaseResponseModel):
    artifact_revisions: list[ArtifactRevisionResponseData]


class CancelImportArtifactResponse(BaseResponseModel):
    artifact_revision: ArtifactRevisionResponseData


class ApproveArtifactRevisionResponse(BaseResponseModel):
    artifact_revision: ArtifactRevisionResponseData


class RejectArtifactRevisionResponse(BaseResponseModel):
    artifact_revision: ArtifactRevisionResponseData


class ArtifactRevisionImportTask(BaseResponseModel):
    task_id: str
    artifact_revision: ArtifactRevisionResponseData


class ImportArtifactsResponse(BaseResponseModel):
    tasks: list[ArtifactRevisionImportTask]


class UpdateArtifactResponse(BaseResponseModel):
    artifact: ArtifactData


class GetArtifactRevisionReadmeResponse(BaseResponseModel):
    readme: Optional[str]
