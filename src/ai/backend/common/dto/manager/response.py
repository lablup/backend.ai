from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.field import VFolderItemField


class VFolderCreateResponse(BaseResponseModel):
    item: VFolderItemField


class VFolderListResponse(BaseResponseModel):
    items: list[VFolderItemField] = Field(default_factory=list)
