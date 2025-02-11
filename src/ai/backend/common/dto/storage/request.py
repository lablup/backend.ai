from pathlib import PurePosixPath
from typing import Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from ai.backend.common.dto.identifiers import VolumeID
from ai.backend.common.types import QuotaConfig, QuotaScopeID, VFolderID


class _BaseModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


VOLUME_ID_FIELD = Field(
    validation_alias=AliasChoices(
        "volume",
        "volumeid",
        "volume_id",
        "volumeId",
    ),
    description="A unique identifier for the volume.",
)
VFOLDER_ID_FIELD = Field(
    validation_alias=AliasChoices(
        "vfid",
        "folderid",
        "folder_id",
        "folderId",
        "vfolderid",
        "vfolder_id",
        "vfolderId",
    ),
    description="A unique identifier for the virtual folder.",
)
QUOTA_SCOPE_ID_FIELD = Field(
    validation_alias=AliasChoices(
        "qsid",
        "quotascopeid",
        "quota_scope_id",
        "quotaScopeId",
    ),
    description="A unique identifier for the quota scope.",
)


class VolumeKeyDataParams(_BaseModel):
    volume_id: VolumeID = VOLUME_ID_FIELD


class VFolderKeyDataParams(_BaseModel):
    volume_id: VolumeID = VOLUME_ID_FIELD
    vfolder_id: VFolderID = VFOLDER_ID_FIELD
    subpath: Optional[PurePosixPath] = Field(default=None)
    # You can use volume_id and vfolder_id as src_volume and src_vfolder_id.
    dst_vfolder_id: Optional[VFolderID] = Field(
        default=None,
        validation_alias=AliasChoices(
            "dst_vfid",
            "dstvfolderid",
            "dst_vfolder_id",
            "dstVfolderId",
        ),
    )


class QuotaScopeKeyDataParams(_BaseModel):
    volume_id: VolumeID = VOLUME_ID_FIELD
    quota_scope_id: QuotaScopeID = QUOTA_SCOPE_ID_FIELD
    options: Optional[QuotaConfig] = Field(default=None)
