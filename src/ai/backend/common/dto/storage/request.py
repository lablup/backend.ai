from typing import Optional

from pydantic import AliasChoices, Field

from ...api_handlers import BaseRequestModel
from ...types import QuotaConfig, VFolderID


class QuotaScopeReq(BaseRequestModel):
    options: Optional[QuotaConfig] = Field(
        default=None,
        description="The options for the quota scope.",
    )


class GetVFolderMetaReq(BaseRequestModel):
    subpath: str = Field(
        description="The subpath of the virtual folder.",
    )


class CloneVFolderReq(BaseRequestModel):
    dst_vfolder_id: VFolderID = Field(
        description="The destination virtual folder ID.",
        validation_alias=AliasChoices("dst_vfid", "dst_vfolder_id"),
    )
