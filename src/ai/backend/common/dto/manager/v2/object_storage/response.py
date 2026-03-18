"""
Response DTOs for object_storage DTO v2.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "BucketsPayload",
    "CreateObjectStoragePayload",
    "DeleteObjectStoragePayload",
    "ObjectStorageNode",
    "PresignedDownloadURLPayload",
    "PresignedUploadURLPayload",
    "UpdateObjectStoragePayload",
)


class ObjectStorageNode(BaseResponseModel):
    """Node model representing an object storage entity."""

    id: UUID = Field(description="Object storage ID")
    name: str = Field(description="Object storage name")
    host: str = Field(description="Host address of the object storage")
    access_key: str = Field(description="Access key for authentication")
    secret_key: str = Field(description="Secret key for authentication")
    endpoint: str = Field(description="Endpoint URL of the object storage")
    region: str | None = Field(default=None, description="Region of the object storage")


class CreateObjectStoragePayload(BaseResponseModel):
    """Payload for object storage creation mutation result."""

    object_storage: ObjectStorageNode = Field(description="Created object storage")


class UpdateObjectStoragePayload(BaseResponseModel):
    """Payload for object storage update mutation result."""

    object_storage: ObjectStorageNode = Field(description="Updated object storage")


class DeleteObjectStoragePayload(BaseResponseModel):
    """Payload for object storage deletion mutation result."""

    id: UUID = Field(description="ID of the deleted object storage")


class PresignedUploadURLPayload(BaseResponseModel):
    """Payload for presigned upload URL generation result."""

    presigned_url: str = Field(description="Presigned URL for uploading")
    fields: str = Field(description="Additional fields required for the upload request")


class PresignedDownloadURLPayload(BaseResponseModel):
    """Payload for presigned download URL generation result."""

    presigned_url: str = Field(description="Presigned URL for downloading")


class BucketsPayload(BaseResponseModel):
    """Payload for listing buckets in an object storage."""

    buckets: list[str] = Field(description="List of bucket names")
