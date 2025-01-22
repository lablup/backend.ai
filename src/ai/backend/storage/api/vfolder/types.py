import uuid
from pathlib import Path, PurePath, PurePosixPath
from typing import Any, Mapping, TypeAlias

from pydantic import AliasChoices, Field, model_validator
from pydantic import BaseModel as PydanticBaseModel

from ai.backend.common.types import BinarySize, QuotaConfig, QuotaScopeID, VFolderID
from ai.backend.storage.types import CapacityUsage, TreeUsage

__all__ = (
    "VolumeIDModel",
    "VolumeInfoModel",
    "VolumeInfoListModel",
    "VFolderIDModel",
    "VFolderInfoRequestModel",
    "VFolderInfoModel",
    "VFolderCloneModel",
    "QuotaIDModel",
    "QuotaScopeInfoModel",
    "QuotaConfigModel",
)


class BaseModel(PydanticBaseModel):
    """Base model for all models in this module"""

    model_config = {"arbitrary_types_allowed": True}


VolumeID: TypeAlias = uuid.UUID


# Common fields for VolumeID and VFolderID
VOLUME_ID_FIELD = Field(
    ...,
    validation_alias=AliasChoices(
        "vid", "volumeid", "volume_id", "VolumeID", "Volume_Id", "Volumeid"
    ),
)
VFOLDER_ID_FIELD = Field(
    ...,
    validation_alias=AliasChoices(
        "vfid", "vfolderid", "vfolder_id", "VFolderID", "VFolder_Id", "VFolderid"
    ),
)
QUOTA_SCOPE_ID_FIELD = Field(
    ...,
    validation_alias=AliasChoices(
        "qsid",
        "quotascopeid",
        "quota_scope_id",
        "QuotaScopeID",
        "Quota_Scope_Id",
        "QuotaScopeid",
        "Quota_ScopeID",
        "Quota_Scopeid",
        "quotaScopeID",
        "quotaScopeid",
    ),
)


class VolumeIDModel(BaseModel):
    volume_id: VolumeID = VOLUME_ID_FIELD

    @model_validator(mode="before")
    def validate_all_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
        if "volume_id" in values and not isinstance(values["volume_id"], uuid.UUID):
            raise ValueError("volume_id must be a UUID")
        return values


class VolumeInfoModel(BaseModel):
    """For `get_volume`, `get_volumes` requests"""

    volume_id: VolumeID = VOLUME_ID_FIELD
    backend: str = Field(...)
    path: Path = Field(...)
    fsprefix: PurePath | None
    capabilities: list[str] = Field(...)
    options: Mapping[str, Any] | None

    @model_validator(mode="before")
    def validate_all_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
        if "volume_id" in values and not isinstance(values["volume_id"], uuid.UUID):
            raise ValueError("volume_id must be a UUID")
        if "backend" in values and not isinstance(values["backend"], str):
            raise ValueError("backend must be a string")
        if "path" in values and not isinstance(values["path"], Path):
            raise ValueError("path must be a Path object")
        if values.get("fsprefix") is not None and not isinstance(values["fsprefix"], PurePath):
            raise ValueError("fsprefix must be a PurePath or None")
        if "capabilities" in values and not isinstance(values["capabilities"], list):
            raise ValueError("capabilities must be a list of strings")
        if values.get("options") is not None and not isinstance(values["options"], Mapping):
            raise ValueError("options must be a mapping or None")
        return values


class VolumeInfoListModel(BaseModel):
    """For `get_volumes` response"""

    volumes: dict[VolumeID, VolumeInfoModel] = Field(...)

    @model_validator(mode="before")
    def validate_all_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
        if "volumes" in values and not isinstance(values["volumes"], dict):
            raise ValueError("volumes must be a dictionary")
        for k, v in values.get("volumes", {}).items():
            if not isinstance(k, uuid.UUID):
                raise ValueError("keys in volumes must be UUIDs")
            if not isinstance(v, VolumeInfoModel):
                raise ValueError("values in volumes must be VolumeInfoModel instances")
        return values


class VFolderIDModel(BaseModel):
    volume_id: VolumeID = VOLUME_ID_FIELD
    vfolder_id: VFolderID = VFOLDER_ID_FIELD

    @model_validator(mode="before")
    def validate_all_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
        if "volume_id" in values and not isinstance(values["volume_id"], uuid.UUID):
            raise ValueError("volume_id must be a UUID")
        if "vfolder_id" in values and not isinstance(values["vfolder_id"], VFolderID):
            raise ValueError("vfolder_id must be a VFolderID")
        return values


class VFolderInfoRequestModel(BaseModel):
    """For `get_vfolder_info` request"""

    volume_id: VolumeID = VOLUME_ID_FIELD
    vfolder_id: VFolderID = VFOLDER_ID_FIELD
    subpath: PurePosixPath = Field(...)

    @model_validator(mode="before")
    def validate_all_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
        if "volume_id" in values and not isinstance(values["volume_id"], uuid.UUID):
            raise ValueError("volume_id must be a UUID")
        if "vfolder_id" in values and not isinstance(values["vfolder_id"], VFolderID):
            raise ValueError("vfolder_id must be a VFolderID")
        if "subpath" in values and not isinstance(values["subpath"], PurePosixPath):
            raise ValueError("subpath must be a PurePosixPath")
        return values


class VFolderInfoModel(BaseModel):
    """For `get_vfolder_info` response"""

    vfolder_mount: Path = Field(...)
    vfolder_metadata: bytes = Field(...)  # 실제로 쓰이는지 확인 필요
    vfolder_usage: TreeUsage = Field(...)
    vfolder_used_bytes: BinarySize = Field(...)
    vfolder_fs_usage: CapacityUsage = Field(...)

    @model_validator(mode="before")
    def validate_all_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
        if "vfolder_mount" in values and not isinstance(values["vfolder_mount"], Path):
            raise ValueError("vfolder_mount must be a Path object")
        if "vfolder_metadata" in values and not isinstance(values["vfolder_metadata"], bytes):
            raise ValueError("vfolder_metadata must be bytes")
        if "vfolder_usage" in values and not isinstance(values["vfolder_usage"], TreeUsage):
            raise ValueError("vfolder_usage must be a TreeUsage object")
        if "vfolder_used_bytes" in values and not isinstance(
            values["vfolder_used_bytes"], BinarySize
        ):
            raise ValueError("vfolder_used_bytes must be a BinarySize object")
        if "vfolder_fs_usage" in values and not isinstance(
            values["vfolder_fs_usage"], CapacityUsage
        ):
            raise ValueError("vfolder_fs_usage must be a CapacityUsage object")
        return values


class VFolderCloneModel(BaseModel):
    volume_id: VolumeID = VOLUME_ID_FIELD  # source volume
    src_vfolder_id: VFolderID = Field(
        ...,
        validation_alias=AliasChoices(
            "src_vfid",
            "src_vfolderid",
            "src_vfolder_id",
            "source",
            "src",
            "src_vfolderid",
            "source_vfid",
            "source_vfolderid",
            "source_vfolder_id",
            "SrcVfid",
            "SrcVfolderid",
            "Source",
            "Src",
            "SrcVfolderid",
            "SourceVfid",
            "SourceVfolderid",
        ),
    )
    dst_vfolder_id: VFolderID = Field(
        ...,
        validation_alias=AliasChoices(
            "dst_vfid",
            "dst_vfolderid",
            "destination",
            "dst",
            "dst_vfolderid",
            "dst_vfolder_id",
            "destination_vfid",
            "destination_vfolderid",
            "destination_vfolder_id",
            "DstVfid",
            "DstVfolderid",
            "Destination",
            "Dst",
            "DstVfolderid",
            "DestinationVfid",
            "DestinationVfolderid",
        ),
    )

    @model_validator(mode="before")
    def validate_all_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
        if "volume_id" in values and not isinstance(values["volume_id"], uuid.UUID):
            raise ValueError("volume_id must be a UUID")
        if "src_vfolder_id" in values and not isinstance(values["src_vfolder_id"], VFolderID):
            raise ValueError("src_vfolder_id must be a VFolderID")
        if "dst_vfolder_id" in values and not isinstance(values["dst_vfolder_id"], VFolderID):
            raise ValueError("dst_vfolder_id must be a VFolderID")
        return values


class QuotaIDModel(BaseModel):
    volume_id: VolumeID = VOLUME_ID_FIELD
    quota_scope_id: QuotaScopeID = QUOTA_SCOPE_ID_FIELD

    @model_validator(mode="before")
    def validate_all_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
        if "volume_id" in values and not isinstance(values["volume_id"], uuid.UUID):
            raise ValueError("volume_id must be a UUID")
        if "quota_scope_id" in values and not isinstance(values["quota_scope_id"], QuotaScopeID):
            raise ValueError("quota_scope_id must be a QuotaScopeID")
        return values


class QuotaScopeInfoModel(BaseModel):
    used_bytes: int | None
    limit_bytes: int | None

    @model_validator(mode="before")
    def validate_all_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
        for field in ["used_bytes", "limit_bytes"]:
            value = values.get(field)
            if value is None:
                values[field] = 0
            elif not isinstance(value, int):
                raise ValueError(f"{field} must be an integer or None")
        return values


class QuotaConfigModel(BaseModel):
    volume_id: VolumeID = VOLUME_ID_FIELD
    quota_scope_id: QuotaScopeID = QUOTA_SCOPE_ID_FIELD
    options: QuotaConfig | None

    @model_validator(mode="before")
    def validate_all_fields(cls, values: dict[str, Any]) -> dict[str, Any]:
        if "volume_id" in values and not isinstance(values["volume_id"], uuid.UUID):
            raise ValueError("volume_id must be a UUID")
        if "quota_scope_id" in values and not isinstance(values["quota_scope_id"], QuotaScopeID):
            raise ValueError("quota_scope_id must be a QuotaScopeID")
        if values.get("options") is not None and not isinstance(values["options"], QuotaConfig):
            raise ValueError("options must be a QuotaConfig or None")
        return values
