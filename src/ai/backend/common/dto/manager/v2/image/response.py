"""
Response DTOs for image DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.dto.manager.pagination import PaginationInfo

from .types import (
    ImageLabelInfo,
    ImageResourceLimitInfo,
    ImageStatusType,
    ImageTagInfo,
    ImageTypeEnum,
)

__all__ = (
    "AdminSearchImagesPayload",
    "AliasImagePayload",
    "ForgetImagePayload",
    "GetImagePayload",
    "ImageNode",
    "PurgeImagePayload",
    "RescanImagesPayload",
    "SearchImagesPayload",
)


class ImageNode(BaseResponseModel):
    """Node model representing an image entity with full details."""

    id: UUID = Field(description="Image ID")
    name: str = Field(description="Image canonical name")
    registry: str = Field(description="Registry hostname")
    registry_id: UUID = Field(description="Registry ID")
    project: str | None = Field(default=None, description="Project (namespace) within registry")
    tag: str | None = Field(default=None, description="Image tag")
    architecture: str = Field(description="Target CPU architecture")
    size_bytes: int = Field(description="Image size in bytes")
    type: ImageTypeEnum = Field(description="Image type category")
    status: ImageStatusType = Field(description="Image status")
    labels: list[ImageLabelInfo] = Field(default_factory=list, description="Image labels")
    tags: list[ImageTagInfo] = Field(default_factory=list, description="Image tags")
    resource_limits: list[ImageResourceLimitInfo] = Field(
        default_factory=list, description="Resource limit definitions per resource slot"
    )
    accelerators: str | None = Field(default=None, description="Accelerator requirement string")
    config_digest: str = Field(description="Image config digest")
    is_local: bool = Field(description="Whether the image is local-only")
    created_at: datetime | None = Field(default=None, description="Image creation timestamp")


class SearchImagesPayload(BaseResponseModel):
    """Payload for image search result."""

    items: list[ImageNode] = Field(description="List of matching images")
    pagination: PaginationInfo = Field(description="Pagination information")


class GetImagePayload(BaseResponseModel):
    """Payload for single image retrieval result."""

    item: ImageNode = Field(description="Retrieved image")


class RescanImagesPayload(BaseResponseModel):
    """Payload for image rescan result."""

    item: ImageNode = Field(description="Rescanned image")
    errors: list[str] = Field(default_factory=list, description="Errors encountered during rescan")


class AliasImagePayload(BaseResponseModel):
    """Payload for image alias creation result."""

    alias_id: UUID = Field(description="Created alias ID")
    alias: str = Field(description="Alias name")
    image_id: UUID = Field(description="ID of the aliased image")


class ForgetImagePayload(BaseResponseModel):
    """Payload for image forget (soft-delete) result."""

    item: ImageNode = Field(description="Forgotten image")


class PurgeImagePayload(BaseResponseModel):
    """Payload for image purge (hard-delete) result."""

    item: ImageNode = Field(description="Purged image")


class AdminSearchImagesPayload(BaseResponseModel):
    """Payload for admin-scoped paginated image search results."""

    items: list[ImageNode] = Field(description="List of image nodes.")
    total_count: int = Field(description="Total number of images matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")
