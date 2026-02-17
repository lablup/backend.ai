"""
Response DTOs for image management REST API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "AliasImageResponse",
    "ForgetImageResponse",
    "GetImageResponse",
    "ImageDTO",
    "PaginationInfo",
    "PurgeImageResponse",
    "RescanImagesResponse",
    "SearchImagesResponse",
)


class ImageTagEntryDTO(BaseModel):
    """A single parsed tag component from the image reference."""

    key: str = Field(description="Tag key")
    value: str = Field(description="Tag value")


class ImageLabelEntryDTO(BaseModel):
    """A single label from the image metadata."""

    key: str = Field(description="Label key")
    value: str = Field(description="Label value")


class ImageResourceLimitDTO(BaseModel):
    """Resource limit for an image."""

    key: str = Field(description="Resource slot name")
    min: Decimal = Field(description="Minimum limit")
    max: Decimal = Field(description="Maximum limit")


class ImageDTO(BaseModel):
    """DTO for image data."""

    id: UUID = Field(description="Image ID")
    name: str = Field(description="Canonical image name")
    registry: str = Field(description="Registry hostname")
    registry_id: UUID = Field(description="Registry ID")
    project: str | None = Field(default=None, description="Registry project/namespace")
    tag: str | None = Field(default=None, description="Image tag")
    architecture: str = Field(description="Image architecture")
    size_bytes: int = Field(description="Image size in bytes")
    type: str = Field(description="Image type (compute/system/service)")
    status: str = Field(description="Image status (ALIVE/DELETED)")
    labels: list[ImageLabelEntryDTO] = Field(default_factory=list, description="Image labels")
    tags: list[ImageTagEntryDTO] = Field(default_factory=list, description="Parsed tag components")
    resource_limits: list[ImageResourceLimitDTO] = Field(
        default_factory=list, description="Resource limits"
    )
    accelerators: str | None = Field(default=None, description="Supported accelerators")
    config_digest: str = Field(description="Image config digest")
    is_local: bool = Field(description="Whether the image is local")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")


class PaginationInfo(BaseModel):
    """Pagination information."""

    total: int = Field(description="Total number of items")
    offset: int = Field(description="Number of items skipped")
    limit: int | None = Field(default=None, description="Maximum items returned")


class SearchImagesResponse(BaseResponseModel):
    """Response for searching images."""

    items: list[ImageDTO] = Field(description="List of images")
    pagination: PaginationInfo = Field(description="Pagination information")


class GetImageResponse(BaseResponseModel):
    """Response for getting a single image."""

    item: ImageDTO = Field(description="Image data")


class RescanImagesResponse(BaseResponseModel):
    """Response for rescanning images."""

    item: ImageDTO = Field(description="Rescanned image data")
    errors: list[str] = Field(default_factory=list, description="Errors during rescan")


class AliasImageResponse(BaseResponseModel):
    """Response for creating an image alias."""

    alias_id: UUID = Field(description="Created alias ID")
    alias: str = Field(description="Alias name")
    image_id: UUID = Field(description="Associated image ID")


class ForgetImageResponse(BaseResponseModel):
    """Response for forgetting an image."""

    item: ImageDTO = Field(description="Forgotten image data")


class PurgeImageResponse(BaseResponseModel):
    """Response for purging an image."""

    item: ImageDTO = Field(description="Purged image data")
