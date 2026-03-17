"""
Request DTOs for image DTO v2.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter

from .types import ImageOrderField, OrderDirection

__all__ = (
    "AdminSearchImagesInput",
    "AliasImageInput",
    "DealiasImageInput",
    "ForgetImageInput",
    "ImageFilter",
    "ImageOrder",
    "PurgeImageInput",
    "RescanImagesInput",
    "SearchImagesInput",
)


class ImageFilter(BaseRequestModel):
    """Filter conditions for image search."""

    name: StringFilter | None = Field(default=None, description="Filter by image name")
    architecture: StringFilter | None = Field(default=None, description="Filter by architecture")


class ImageOrder(BaseRequestModel):
    """Order specification for image search."""

    field: ImageOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")


class SearchImagesInput(BaseRequestModel):
    """Input for searching images with filters, orders, and pagination."""

    filter: ImageFilter | None = Field(default=None, description="Filter conditions")
    order: list[ImageOrder] | None = Field(default=None, description="Order specifications")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class RescanImagesInput(BaseRequestModel):
    """Input for rescanning images from a registry."""

    canonical: str = Field(min_length=1, description="Image canonical name to rescan")
    architecture: str = Field(min_length=1, description="Image architecture to rescan")


class AliasImageInput(BaseRequestModel):
    """Input for creating an image alias."""

    image_id: UUID = Field(description="ID of the image to alias")
    alias: str = Field(min_length=1, max_length=256, description="Alias name to assign")

    @field_validator("alias")
    @classmethod
    def alias_must_not_be_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("alias must not be blank or whitespace-only")
        return stripped


class DealiasImageInput(BaseRequestModel):
    """Input for removing an image alias."""

    alias: str = Field(min_length=1, description="Alias name to remove")


class ForgetImageInput(BaseRequestModel):
    """Input for forgetting (soft-deleting) an image."""

    image_id: UUID = Field(description="ID of the image to forget")


class PurgeImageInput(BaseRequestModel):
    """Input for purging (hard-deleting) an image."""

    image_id: UUID = Field(description="ID of the image to purge")


class AdminSearchImagesInput(BaseRequestModel):
    """Input for admin search of images with cursor and offset pagination."""

    filter: ImageFilter | None = Field(default=None, description="Filter conditions.")
    order: list[ImageOrder] | None = Field(default=None, description="Order specifications.")
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")
