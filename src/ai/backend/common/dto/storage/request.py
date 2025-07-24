from typing import Literal, Optional

from pydantic import Field

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
        alias="dst_vfid",
    )


class S3TokenData(BaseRequestModel):
    """JWT token data for S3 storage operations."""

    op: Literal["upload", "download", "info", "delete", "presigned_upload", "presigned_download"]
    bucket: str
    key: str
    expiration: Optional[int] = Field(default=None, gt=0, le=604800)
    content_type: Optional[str] = None
    min_size: Optional[int] = Field(default=None, ge=0)
    max_size: Optional[int] = Field(default=None, gt=0)
    filename: Optional[str] = None
