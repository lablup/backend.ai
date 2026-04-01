"""
Request DTOs for image management REST API.
Shared between Client SDK and Manager API.
"""

from __future__ import annotations

import uuid

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter

from .types import (
    ImageOrderField,
    OrderDirection,
)

__all__ = (
    "AliasImageRequest",
    "DealiasImageRequest",
    "ForgetImageRequest",
    "GetImageRequest",
    "ImageFilter",
    "ImageOrder",
    "PurgeImageRequest",
    "RescanImagesRequest",
    "SearchImagesRequest",
    "StringFilter",
)


class ImageFilter(BaseRequestModel):
    """Filter for images."""

    name: StringFilter | None = Field(default=None, description="Filter by image name")
    architecture: StringFilter | None = Field(default=None, description="Filter by architecture")


class ImageOrder(BaseRequestModel):
    """Order specification for images."""

    field: ImageOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class SearchImagesRequest(BaseRequestModel):
    """Request body for searching images with filters, orders, and pagination."""

    filter: ImageFilter | None = Field(default=None, description="Filter conditions")
    order: list[ImageOrder] | None = Field(default=None, description="Order specifications")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class GetImageRequest(BaseRequestModel):
    """Request body for getting an image (unused — path param only)."""


class RescanImagesRequest(BaseRequestModel):
    """Request body for rescanning images from a registry."""

    canonical: str = Field(description="Image canonical name to rescan")
    architecture: str = Field(description="Image architecture to rescan")


class AliasImageRequest(BaseRequestModel):
    """Request body for creating an image alias."""

    image_id: uuid.UUID = Field(description="ID of the image to alias")
    alias: str = Field(description="Alias name to assign")


class DealiasImageRequest(BaseRequestModel):
    """Request body for removing an image alias."""

    alias: str = Field(description="Alias name to remove")


class ForgetImageRequest(BaseRequestModel):
    """Request body for forgetting (soft-deleting) an image."""

    image_id: uuid.UUID = Field(description="ID of the image to forget")


class PurgeImageRequest(BaseRequestModel):
    """Request body for purging (hard-deleting) an image."""

    image_id: uuid.UUID = Field(description="ID of the image to purge")
