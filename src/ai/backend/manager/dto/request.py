import uuid
from typing import Optional

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.manager.types import PaginationOptions


class ArtifactRegistriesScanReq(BaseRequestModel):
    storage_id: uuid.UUID = Field(description="The unique identifier of the storage to scan.")
    registry_id: uuid.UUID = Field(
        description="The unique identifier of the artifact registry to scan."
    )
    limit: int
    search: Optional[str] = None


class ArtifactRegistriesSearchReq(BaseRequestModel):
    pagination: PaginationOptions
    # TODO: Support this. (we need to make strawberry independent types)
    # ordering: Optional[ArtifactOrderingOptions] = None
    # filters: Optional[ArtifactFilterOptions] = None
