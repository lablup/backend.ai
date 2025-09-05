from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.manager.data.artifact.types import ArtifactDataWithRevisions, ArtifactRevisionData


class SearchArtifactsResponse(BaseResponseModel):
    artifacts: list[ArtifactDataWithRevisions]


class ScanArtifactModelsResponse(BaseResponseModel):
    artifacts: list[ArtifactDataWithRevisions]


class CleanupArtifactsResponse(BaseResponseModel):
    artifact_revisions: list[ArtifactRevisionData]
