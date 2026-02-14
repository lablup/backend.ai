"""
Response DTOs for storage domain.

Covers object storage and VFS storage response models.
"""

import uuid

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    # Object storage models (from common/dto/manager/response.py)
    "ObjectStorageResponse",
    "ObjectStorageListResponse",
    # Presigned URL models (from common/dto/manager/response.py)
    "GetPresignedDownloadURLResponse",
    "GetPresignedUploadURLResponse",
    # Object storage bucket models (from common/dto/manager/response.py)
    "ObjectStorageBucketsResponse",
    "ObjectStorageAllBucketsResponse",
    # VFS storage models (from manager/dto/response.py)
    "VFSStorage",
    "GetVFSStorageResponse",
    "ListVFSStorageResponse",
)


# ---------------------------------------------------------------------------
# Object storage models (from common/dto/manager/response.py)
# ---------------------------------------------------------------------------


class ObjectStorageResponse(BaseResponseModel):
    id: str = Field(description="ID of the object storage")
    name: str = Field(description="Name of the object storage")
    host: str = Field(description="Host address of the object storage")
    access_key: str = Field(description="Access key for authentication")
    secret_key: str = Field(description="Secret key for authentication")
    endpoint: str = Field(description="Endpoint URL of the object storage")
    region: str = Field(description="Region of the object storage")


class ObjectStorageListResponse(BaseResponseModel):
    storages: list[ObjectStorageResponse] = Field(description="List of object storages")


# ---------------------------------------------------------------------------
# Presigned URL models (from common/dto/manager/response.py)
# ---------------------------------------------------------------------------


class GetPresignedDownloadURLResponse(BaseResponseModel):
    presigned_url: str = Field(description="The presigned download URL")


class GetPresignedUploadURLResponse(BaseResponseModel):
    presigned_url: str = Field(description="The presigned upload URL")
    fields: str = Field(description="JSON string containing the form fields")


# ---------------------------------------------------------------------------
# Object storage bucket models (from common/dto/manager/response.py)
# ---------------------------------------------------------------------------


class ObjectStorageBucketsResponse(BaseResponseModel):
    buckets: list[str] = Field(description="List of bucket names for a specific storage")


class ObjectStorageAllBucketsResponse(BaseResponseModel):
    buckets_by_storage: dict[uuid.UUID, list[str]] = Field(
        description="Mapping of storage IDs to bucket lists"
    )


# ---------------------------------------------------------------------------
# VFS storage models (from manager/dto/response.py)
# ---------------------------------------------------------------------------


class VFSStorage(BaseModel):
    name: str
    base_path: str
    host: str


class GetVFSStorageResponse(BaseResponseModel):
    storage: VFSStorage


class ListVFSStorageResponse(BaseResponseModel):
    storages: list[VFSStorage]
