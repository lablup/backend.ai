from uuid import UUID

from pydantic import Field

from ...api_handlers import BaseRequestModel
from ...types import QuotaScopeType, VolumeID


class VolumeIDPath(BaseRequestModel):
    volume_id: VolumeID = Field(
        description="A unique identifier for the volume.",
    )


class QuotaScopeKeyPath(VolumeIDPath):
    quota_scope_type: QuotaScopeType = Field(
        description="The type of the quota scope.",
    )
    quota_scope_uuid: UUID = Field(
        description="A unique uuid for the quota scope.",
    )


class VFolderKeyPath(QuotaScopeKeyPath):
    folder_uuid: UUID = Field(
        description="A unique uuid for the virtual folder.",
    )
