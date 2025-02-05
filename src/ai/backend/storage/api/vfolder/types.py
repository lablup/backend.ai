import uuid
from pathlib import Path, PurePath, PurePosixPath
from typing import List, Optional, TypeAlias

from pydantic import AliasChoices, Field
from pydantic import BaseModel as PydanticBaseModel

from ai.backend.common.types import BinarySize, QuotaConfig, QuotaScopeID, VFolderID


class BaseModel(PydanticBaseModel):
    """Base model for all models in this module"""

    model_config = {"arbitrary_types_allowed": True}


VolumeID: TypeAlias = uuid.UUID


# Common fields for VolumeID and VFolderID
VOLUME_ID_FIELD = Field(
    ...,
    validation_alias=AliasChoices(
        "volume",
        "volumeid",
        "volume_id",
        "volumeId",
    ),
    description="A unique identifier for the volume.",
)
VFOLDER_ID_FIELD = Field(
    ...,
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
    ...,
    validation_alias=AliasChoices(
        "qsid",
        "quotascopeid",
        "quota_scope_id",
        "quotaScopeId",
    ),
    description="A unique identifier for the quota scope.",
)


class VolumeIdData(BaseModel):
    volume_id: VolumeID = VOLUME_ID_FIELD


class VolumeMetadata(BaseModel):
    """For `get_volume`, `get_volumes`"""

    volume_id: VolumeID = Field(..., description="The unique identifier for the volume.")
    backend: str = Field(
        ..., description="The backend storage type for the volume (e.g., CephFS, GPFS)."
    )
    path: Path = Field(..., description="The path where the volume is mounted.")
    fsprefix: Optional[PurePath] = Field(
        default=None, description="The filesystem prefix for the volume, or None if not applicable."
    )
    capabilities: list[str] = Field(
        ..., description="A list of capabilities supported by the volume."
    )


class VolumeMetadataList(BaseModel):
    volumes: List[VolumeMetadata] = Field(..., description="A list of volume information.")


class VFolderIdData(BaseModel):
    volume_id: VolumeID = VOLUME_ID_FIELD
    vfolder_id: VFolderID = VFOLDER_ID_FIELD
    # For `get_vfolder_info`: mount
    subpath: Optional[PurePosixPath] = Field(
        default=None,
        description="For `get_vfolder_info`\n\
            The subpath inside the virtual folder to be queried.",
    )
    # For `clone_vfolder`
    # You can use volume_id and vfolder_id as src_volume and src_vfolder_id.
    dst_vfolder_id: Optional[VFolderID] = Field(
        default=None,
        validation_alias=AliasChoices(
            "dst_vfid",
            "dstvfolderid",
            "dst_vfolder_id",
            "dstVfolderId",
        ),
        description="For `clone_vfolder`\n\
            The destination virtual folder ID to clone to.",
    )


class VFolderMetadata(BaseModel):
    """For `get_vfolder_info`"""

    mount_path: Path = Field(..., description="The path where the virtual folder is mounted.")
    file_count: int = Field(..., description="The number of files in the virtual folder.")
    capacity_bytes: int = Field(
        ..., description="The total capacity in bytes of the virtual folder."
    )
    used_bytes: BinarySize = Field(
        ..., description="The amount of used bytes in the virtual folder."
    )


class QuotaScopeIdData(BaseModel):
    volume_id: VolumeID = VOLUME_ID_FIELD
    quota_scope_id: QuotaScopeID = QUOTA_SCOPE_ID_FIELD
    options: Optional[QuotaConfig] = Field(
        default=None, description="Optional configuration settings for the quota."
    )


class QuotaScopeMetadata(BaseModel):
    """For `get_quota_scope`"""

    used_bytes: Optional[int] = Field(
        default=0, description="The number of bytes currently used in the quota scope."
    )
    limit_bytes: Optional[int] = Field(
        default=0, description="The maximum number of bytes allowed in the quota scope."
    )
