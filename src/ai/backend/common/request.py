from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VolumeRequest(BaseModel):
    volume: str = Field(description="Volume name")


class VolumePerformanceMetricRequest(VolumeRequest):
    pass


class VolumeHwinfoRequest(VolumeRequest):
    pass


class VolumeFsUsageRequest(VolumeRequest):
    pass


class VolumeQuotaRequest(VolumeRequest):
    pass


class VolumeQuotaUpdateRequest(VolumeRequest):
    quota: int = Field(description="Quota limit in bytes")


class FolderRequest(BaseModel):
    volume: str = Field(description="Volume name")
    vfid: str = Field(description="Virtual folder ID")


class FolderCreateRequest(FolderRequest):
    options: Optional[Dict[str, Any]] = Field(
        None, description="Additional options for folder creation"
    )
    mode: Optional[int] = Field(None, description="Permission mode for the folder")


class FolderCloneRequest(BaseModel):
    src_volume: str = Field(description="Source volume name")
    src_vfid: str = Field(description="Source virtual folder ID")
    dst_volume: str = Field(description="Destination volume name")
    dst_vfid: str = Field(description="Destination virtual folder ID")
    options: Optional[Dict[str, Any]] = Field(
        None, description="Additional options for folder cloning"
    )


class FolderDeleteRequest(FolderRequest):
    pass


class FolderUsageRequest(FolderRequest):
    pass


class FolderUsedBytesRequest(FolderRequest):
    pass


class FolderMountRequest(FolderRequest):
    subpath: str = Field(default=".", description="Subpath within the folder to mount")


class FolderFileRequest(FolderRequest):
    relpath: str = Field(description="Relative path to the file")


class FolderFileUploadRequest(FolderFileRequest):
    size: int = Field(description="File size in bytes")
    archive: Optional[bool] = Field(None, description="Whether to treat as archive file")


class FolderFileDownloadRequest(FolderFileRequest):
    archive: Optional[bool] = Field(None, description="Whether to download as archive")
    chunks: Optional[List[List[int]]] = Field(
        None, description="Chunk information for partial downloads"
    )


class FolderFileListRequest(FolderRequest):
    relpath: str = Field(default=".", description="Relative path to list files from")


class FolderFileRenameRequest(FolderFileRequest):
    new_relpath: str = Field(description="New relative path for the file")


class FolderFileDeleteRequest(FolderRequest):
    relpaths: List[str] = Field(description="List of relative paths to delete")
    recursive: Optional[bool] = Field(None, description="Whether to delete recursively")


class FolderFileMkdirRequest(FolderRequest):
    relpath: str = Field(description="Relative path for the directory to create")
    parents: Optional[bool] = Field(None, description="Whether to create parent directories")
    exist_ok: Optional[bool] = Field(
        None, description="Whether to ignore if directory already exists"
    )


class FolderFileMoveRequest(FolderRequest):
    src_relpath: str = Field(description="Source relative path")
    dst_relpath: str = Field(description="Destination relative path")


class FolderFileFetchRequest(FolderFileRequest):
    pass


class QuotaScopeRequest(BaseModel):
    volume: str = Field(description="Volume name")
    qsid: str = Field(description="Quota scope ID")


class QuotaScopeUpdateRequest(QuotaScopeRequest):
    options: Dict[str, Any] = Field(description="Quota scope options to update")


class QuotaScopeDeleteQuotaRequest(QuotaScopeRequest):
    pass
