"""
Request DTOs for storage domain.

Covers object storage configuration, presigned URL generation,
and VFS storage management endpoints.
"""

import uuid

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    # Object storage models (from common/dto/manager/request.py)
    "CreateObjectStorageReq",
    "ObjectStoragePathParam",
    "UpdateObjectStorageReq",
    # Presigned URL models (from common/dto/manager/request.py)
    "GetPresignedDownloadURLReq",
    "GetPresignedUploadURLReq",
    # VFS storage models (NEW)
    "VFSStoragePathParam",
    "VFSDownloadFileReq",
    "VFSListFilesReq",
)


# ---------------------------------------------------------------------------
# Object storage models (from common/dto/manager/request.py)
# ---------------------------------------------------------------------------


class CreateObjectStorageReq(BaseRequestModel):
    name: str = Field(description="Name of the object storage")
    host: str = Field(description="Host address of the object storage")
    access_key: str = Field(description="Access key for authentication")
    secret_key: str = Field(description="Secret key for authentication")
    endpoint: str = Field(description="Endpoint URL of the object storage")
    region: str = Field(description="Region of the object storage")


class ObjectStoragePathParam(BaseRequestModel):
    storage_id: uuid.UUID = Field(description="The unique identifier of the object storage.")


class UpdateObjectStorageReq(BaseRequestModel):
    name: str | None = Field(default=None, description="Updated name of the object storage")
    host: str | None = Field(default=None, description="Updated host address")
    access_key: str | None = Field(default=None, description="Updated access key")
    secret_key: str | None = Field(default=None, description="Updated secret key")
    endpoint: str | None = Field(default=None, description="Updated endpoint URL")
    region: str | None = Field(default=None, description="Updated region")


# ---------------------------------------------------------------------------
# Presigned URL models (from common/dto/manager/request.py)
# ---------------------------------------------------------------------------


class GetPresignedDownloadURLReq(BaseRequestModel):
    artifact_revision_id: uuid.UUID = Field(
        description="The unique identifier of the artifact revision"
    )
    key: str = Field(description="Object key")
    expiration: int | None = Field(default=None, description="URL expiration time in seconds")


class GetPresignedUploadURLReq(BaseRequestModel):
    artifact_revision_id: uuid.UUID = Field(
        description="The unique identifier of the artifact revision"
    )
    key: str = Field(description="Object key")
    content_type: str | None = Field(default=None, description="Content type of the object")
    expiration: int | None = Field(default=None, description="URL expiration time in seconds")
    min_size: int | None = Field(default=None, description="Minimum file size")
    max_size: int | None = Field(default=None, description="Maximum file size")


# ---------------------------------------------------------------------------
# VFS storage models (NEW - manager-specific path params)
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
