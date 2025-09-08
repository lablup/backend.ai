from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.manager.data.artifact.types import (
    ArtifactData,
    ArtifactDataWithRevisions,
    ArtifactRevisionData,
)


class SearchArtifactsResponse(BaseResponseModel):
    artifacts: list[ArtifactDataWithRevisions]


class ScanArtifactsResponse(BaseResponseModel):
    artifacts: list[ArtifactDataWithRevisions]


class ScanArtifactModelsResponse(BaseResponseModel):
    artifacts: list[ArtifactDataWithRevisions]


class CleanupArtifactsResponse(BaseResponseModel):
    artifact_revisions: list[ArtifactRevisionData]


class CancelImportArtifactResponse(BaseResponseModel):
    artifact_revision: ArtifactRevisionData


class ApproveArtifactRevisionResponse(BaseResponseModel):
    artifact_revision: ArtifactRevisionData


class RejectArtifactRevisionResponse(BaseResponseModel):
    artifact_revision: ArtifactRevisionData


class ArtifactRevisionImportTask(BaseResponseModel):
    task_id: str
    artifact_revision: ArtifactRevisionData


class ImportArtifactsResponse(BaseResponseModel):
    artifact_revisions: list[ArtifactRevisionData]
    tasks: list[ArtifactRevisionImportTask]


class UpdateArtifactResponse(BaseResponseModel):
    artifact: ArtifactData
