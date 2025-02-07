from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.dto import VFolderItemDTO


class VFolderCreateResponse(BaseResponseModel):
    item: VFolderItemDTO


class VFolderListResponse(BaseResponseModel):
    items: list[VFolderItemDTO] = Field(default_factory=list)
