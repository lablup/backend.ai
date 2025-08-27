from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.manager.data.artifact.types import ArtifactDataWithRevisions


class ArtifactRegistriesScanResponse(BaseResponseModel):
    pass


class ArtifactRegistriesSearchResponse(BaseResponseModel):
    artifacts: list[ArtifactDataWithRevisions]
