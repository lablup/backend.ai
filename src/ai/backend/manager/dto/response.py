from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.manager.data.artifact.types import ArtifactDataWithRevisions


class ScanArtifactsResponse(BaseResponseModel):
    pass


class SearchArtifactsResponse(BaseResponseModel):
    artifacts: list[ArtifactDataWithRevisions]
