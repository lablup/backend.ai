from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class VolumeInfo(BaseModel):
    name: str = Field(description="Volume name")
    backend: str = Field(description="Storage backend type")
    path: str = Field(description="Volume path")
    fsprefix: str = Field(description="Filesystem prefix")
    capabilities: List[str] = Field(description="Volume capabilities")


class VolumesResponse(BaseModel):
    volumes: List[VolumeInfo] = Field(description="List of available volumes")


class VolumePerformanceMetricResponse(BaseModel):
    metric: Dict[str, Any] = Field(description="Performance metrics data")


class VolumeHwinfoResponse(BaseModel):
    capacity: Optional[int] = Field(None, description="Total capacity in bytes")
    used: Optional[int] = Field(None, description="Used space in bytes")


class VolumeFsUsageResponse(BaseModel):
    capacity_bytes: Optional[int] = Field(None, description="Total capacity in bytes")
    used_bytes: Optional[int] = Field(None, description="Used space in bytes")


class VolumeQuotaResponse(BaseModel):
    used: int = Field(description="Used quota in bytes")
    limit: Optional[int] = Field(None, description="Quota limit in bytes")


class FolderUsageResponse(BaseModel):
    file_count: int = Field(description="Number of files in the folder")
    size_bytes: int = Field(description="Total size of files in bytes")


class FolderUsedBytesResponse(BaseModel):
    used_bytes: int = Field(description="Used bytes in the folder")


class FolderMountResponse(BaseModel):
    path: str = Field(description="Mount path for the folder")


class FolderFileUploadResponse(BaseModel):
    token: str = Field(description="Upload token for the file")


class FolderFileDownloadResponse(BaseModel):
    token: str = Field(description="Download token for the file")


class FileItem(BaseModel):
    name: str = Field(description="File or directory name")
    type: str = Field(description="Type of item (file or directory)")
    size: Optional[int] = Field(None, description="File size in bytes")
    mode: Optional[int] = Field(None, description="File permission mode")
    modified: Optional[float] = Field(None, description="Last modified timestamp")
    created: Optional[float] = Field(None, description="Creation timestamp")


class FolderFileListResponse(BaseModel):
    items: List[FileItem] = Field(description="List of files and directories")
    errors: Optional[List[str]] = Field(None, description="List of errors encountered")


class QuotaScopeResponse(BaseModel):
    used: int = Field(description="Used quota in bytes")
    limit: Optional[int] = Field(None, description="Quota limit in bytes")
