"""
Request DTOs for storage domain.

Covers object storage configuration, presigned URL generation,
and VFS storage management endpoints.

Models already defined in ``common.dto.manager.request`` are re-exported here
so that callers can import everything from a single domain-specific path.
"""

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.request import (
    CreateObjectStorageReq,
    GetPresignedDownloadURLReq,
    GetPresignedUploadURLReq,
    ObjectStoragePathParam,
    UpdateObjectStorageReq,
)

__all__ = (
    # Object storage models (re-exported from common.dto.manager.request)
    "CreateObjectStorageReq",
    "ObjectStoragePathParam",
    "UpdateObjectStorageReq",
    # Presigned URL models (re-exported from common.dto.manager.request)
    "GetPresignedDownloadURLReq",
    "GetPresignedUploadURLReq",
    # VFS storage models (NEW)
    "VFSStoragePathParam",
    "VFSDownloadFileReq",
    "VFSListFilesReq",
)


# ---------------------------------------------------------------------------
# VFS storage models (NEW - unique to this module)
# ---------------------------------------------------------------------------


class VFSStoragePathParam(BaseRequestModel):
    """Path parameter for VFS storage manager API endpoints."""

    storage_name: str = Field(description="The name of the VFS storage configuration.")


class VFSDownloadFileReq(BaseRequestModel):
    """Request body for downloading a file from VFS storage."""

    filepath: str = Field(description="The file path within VFS storage to download.")


class VFSListFilesReq(BaseRequestModel):
    """Request body for listing files in a VFS storage directory."""

    directory: str = Field(description="The directory path within VFS storage to list files from.")
