"""
Request DTOs for object_storage DTO v2.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.object_storage.types import (
    ObjectStorageOrderField,
    OrderDirection,
)

__all__ = (
    "AdminSearchObjectStoragesInput",
    "CreateObjectStorageInput",
    "DeleteObjectStorageInput",
    "GetPresignedDownloadURLInput",
    "GetPresignedUploadURLInput",
    "ObjectStorageFilter",
    "ObjectStorageOrder",
    "UpdateObjectStorageInput",
)


class CreateObjectStorageInput(BaseRequestModel):
    """Input for creating an object storage."""

    name: str = Field(min_length=1, max_length=256, description="Object storage name")
    host: str = Field(description="Host address of the object storage")
    access_key: str = Field(description="Access key for authentication")
    secret_key: str = Field(description="Secret key for authentication")
    endpoint: str = Field(description="Endpoint URL of the object storage")
    region: str = Field(description="Region of the object storage")

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("name must not be blank or whitespace-only")
        return stripped


class UpdateObjectStorageInput(BaseRequestModel):
    """Input for updating an object storage."""

    name: str | None = Field(default=None, description="Updated name of the object storage")
    host: str | None = Field(default=None, description="Updated host address")
    access_key: str | None = Field(default=None, description="Updated access key")
    secret_key: str | None = Field(default=None, description="Updated secret key")
    endpoint: str | None = Field(default=None, description="Updated endpoint URL")
    region: str | Sentinel | None = Field(
        default=SENTINEL,
        description="Updated region. Use SENTINEL (default) for no change, None to clear.",
    )


class DeleteObjectStorageInput(BaseRequestModel):
    """Input for deleting an object storage."""

    id: UUID = Field(description="Object storage ID to delete")


class GetPresignedUploadURLInput(BaseRequestModel):
    """Input for getting a presigned upload URL."""

    artifact_revision_id: UUID = Field(description="The unique identifier of the artifact revision")
    key: str = Field(description="Object key")
    content_type: str | None = Field(default=None, description="Content type of the object")
    expiration: int | None = Field(default=None, ge=1, description="URL expiration time in seconds")
    min_size: int | None = Field(default=None, ge=0, description="Minimum file size in bytes")
    max_size: int | None = Field(default=None, ge=0, description="Maximum file size in bytes")


class ObjectStorageFilter(BaseRequestModel):
    """Filter criteria for object storage search."""

    name: StringFilter | None = Field(default=None, description="Filter by storage name.")
    host: StringFilter | None = Field(default=None, description="Filter by storage host.")


class ObjectStorageOrder(BaseRequestModel):
    """Single ordering criterion for object storage search."""

    field: ObjectStorageOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Sort direction.")


class AdminSearchObjectStoragesInput(BaseRequestModel):
    """Input for admin-scoped paginated object storage search."""

    filter: ObjectStorageFilter | None = Field(default=None, description="Filter criteria.")
    order: list[ObjectStorageOrder] | None = Field(default=None, description="Ordering criteria.")
    limit: int | None = Field(default=None, ge=1, description="Maximum number of results.")
    offset: int | None = Field(default=None, ge=0, description="Number of results to skip.")


class GetPresignedDownloadURLInput(BaseRequestModel):
    """Input for getting a presigned download URL."""

    artifact_revision_id: UUID = Field(description="The unique identifier of the artifact revision")
    key: str = Field(description="Object key")
    expiration: int | None = Field(default=None, ge=1, description="URL expiration time in seconds")
