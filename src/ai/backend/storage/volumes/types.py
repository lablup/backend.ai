from pathlib import Path, PurePath, PurePosixPath
from typing import List, Optional

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


class VolumeKeyData(_BaseModel):
    volume_id: VolumeID = VOLUME_ID_FIELD


class VolumeMetadata(_BaseModel):
    volume_id: VolumeID
    backend: str
    path: Path
    fsprefix: Optional[PurePath] = Field(default=None)
    capabilities: list[str]


class VolumeMetadataList(_BaseModel):
    volumes: List[VolumeMetadata]


class VFolderKeyData(_BaseModel):
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


class VFolderMetadata(BaseModel):
    mount_path: Path
    file_count: int
    used_bytes: int
    capacity_bytes: int
    fs_used_bytes: int


class NewVFolderCreated(_BaseModel):
    vfolder_id: VFolderID = VFOLDER_ID_FIELD
    quota_scope_path: Path
    vfolder_path: Path


class QuotaScopeKeyData(_BaseModel):
    volume_id: VolumeID = VOLUME_ID_FIELD
    quota_scope_id: QuotaScopeID = QUOTA_SCOPE_ID_FIELD
    options: Optional[QuotaConfig] = Field(default=None)


class QuotaScopeMetadata(BaseModel):
    used_bytes: Optional[int] = Field(default=0)
    limit_bytes: Optional[int] = Field(default=0)


class NewQuotaScopeCreated(_BaseModel):
    quota_scope_id: QuotaScopeID = QUOTA_SCOPE_ID_FIELD
    quota_scope_path: Path
