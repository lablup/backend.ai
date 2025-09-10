from typing import Optional

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.manager.data.artifact.types import (
    ArtifactData,
    ArtifactDataWithRevisions,
    ArtifactDataWithRevisionsResponse,
    ArtifactRevisionResponseData,
)


class SearchArtifactsResponse(BaseResponseModel):
    artifacts: list[ArtifactDataWithRevisionsResponse]


class ScanArtifactsResponse(BaseResponseModel):
    artifacts: list[ArtifactDataWithRevisionsResponse]


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
