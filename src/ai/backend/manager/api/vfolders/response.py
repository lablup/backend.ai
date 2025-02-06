from typing import Optional, Self

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.types import VFolderUsageMode
from ai.backend.manager.api.vfolders.dtos import (
    VFolderList,
    VFolderListItem,
    VFolderMetadata,
)
from ai.backend.manager.models import (
    VFolderOperationStatus,
)


class VFolderCreateResponse(BaseResponseModel):
    id: str
    name: str
    quota_scope_id: str
    host: str
    usage_mode: VFolderUsageMode
    permission: str
    max_size: int = 0  # migrated to quota scopes, no longer valid
    creator: str
    ownership_type: str
    user: Optional[str]
    group: Optional[str]
    cloneable: bool
    status: VFolderOperationStatus = Field(default=VFolderOperationStatus.READY)

    @classmethod
    def from_vfolder_metadata(cls, data: VFolderMetadata):
        return cls(
            id=data.id,
            name=data.name,
            quota_scope_id=str(data.quota_scope_id),
            host=data.host,
            usage_mode=data.usage_mode,
            permission=data.permission,
            max_size=data.max_size,
            creator=data.creator,
            ownership_type=data.ownership_type,
            user=data.user,
            group=data.group,
            cloneable=data.cloneable,
            status=data.status,
        )


class VFolderListResponse(BaseResponseModel):
    root: list[VFolderListItem] = Field(default_factory=list)

    @classmethod
    def from_dataclass(cls, vfolder_list: VFolderList) -> Self:
        return cls(root=vfolder_list.entries)
