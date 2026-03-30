"""
Request DTOs for image DTO v2.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.manager.query import DateTimeFilter, StringFilter, UUIDFilter

from .types import ImageOrderField, ImageStatusType, OrderDirection

__all__ = (
    "AdminSearchImageAliasesInput",
    "AdminSearchImagesInput",
    "AliasImageInput",
    "ContainerRegistryScopeInputDTO",
    "DealiasImageInput",
    "ForgetImageInput",
    "ImageAliasFilterInputDTO",
    "ImageAliasNestedFilterInputDTO",
    "ImageAliasOrderByInputDTO",
    "ImageFilter",
    "ImageFilterInputDTO",
    "ImageOrder",
    "ImageOrderByInputDTO",
    "ImageScopeInputDTO",
    "ImageStatusFilterInputDTO",
    "PurgeImageInput",
    "RescanImagesInput",
    "SearchImagesInput",
    "UpdateImageInput",
    "UUIDFilter",
)


class ContainerRegistryScopeInputDTO(BaseRequestModel):
    """Scope for querying images within a specific container registry."""

    registry_id: UUID = Field(description="UUID of the container registry to scope the query to.")


class ImageScopeInputDTO(BaseRequestModel):
    """Scope for querying aliases within a specific image."""

    image_id: UUID = Field(description="UUID of the image to scope the query to.")


class ImageStatusFilterInputDTO(BaseRequestModel):
    """Filter for image status."""

    equals: ImageStatusType | None = Field(
        default=None, description="Matches images with this exact status."
    )
    in_: list[ImageStatusType] | None = Field(
        default=None, description="Matches images whose status is in this list."
    )
    not_equals: ImageStatusType | None = Field(
        default=None, description="Excludes images with this exact status."
    )
    not_in: list[ImageStatusType] | None = Field(
        default=None, description="Excludes images whose status is in this list."
    )


class ImageAliasNestedFilterInputDTO(BaseRequestModel):
    """Nested filter for image aliases within an image."""

    alias: StringFilter | None = Field(default=None, description="Filter by alias string.")


class ImageFilterInputDTO(BaseRequestModel):
    """Filter options for images."""

    status: ImageStatusFilterInputDTO | None = Field(default=None, description="Filter by status.")
    name: StringFilter | None = Field(default=None, description="Filter by name.")
    architecture: StringFilter | None = Field(default=None, description="Filter by architecture.")
    registry_id: UUIDFilter | None = Field(
        default=None, description="Filter by container registry ID."
    )
    alias: ImageAliasNestedFilterInputDTO | None = Field(
        default=None, description="Filter by nested alias conditions."
    )
    last_used: DateTimeFilter | None = Field(
        default=None, description="Filter by last used datetime (before/after)."
    )
    AND: list[ImageFilterInputDTO] | None = Field(
        default=None, description="Combine with AND logic."
    )
    OR: list[ImageFilterInputDTO] | None = Field(default=None, description="Combine with OR logic.")
    NOT: list[ImageFilterInputDTO] | None = Field(default=None, description="Negate filters.")


ImageFilterInputDTO.model_rebuild()


class ImageOrderByInputDTO(BaseRequestModel):
    """Order specification for image queries."""

    field: ImageOrderField = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


class ImageAliasFilterInputDTO(BaseRequestModel):
    """Filter options for image aliases."""

    alias: StringFilter | None = Field(default=None, description="Filter by alias string.")
    image_id: UUIDFilter | None = Field(default=None, description="Filter by image ID.")
    AND: list[ImageAliasFilterInputDTO] | None = Field(
        default=None, description="Combine with AND logic."
    )
    OR: list[ImageAliasFilterInputDTO] | None = Field(
        default=None, description="Combine with OR logic."
    )
    NOT: list[ImageAliasFilterInputDTO] | None = Field(default=None, description="Negate filters.")


ImageAliasFilterInputDTO.model_rebuild()


class ImageAliasOrderByInputDTO(BaseRequestModel):
    """Order specification for image alias queries."""

    field: str = Field(description="Field to order by.")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction.")


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

    filter: ImageFilterInputDTO | None = Field(default=None, description="Filter conditions.")
    order: list[ImageOrderByInputDTO] | None = Field(
        default=None, description="Order specifications."
    )
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")


class AdminSearchImageAliasesInput(BaseRequestModel):
    """Input for admin search of image aliases with cursor and offset pagination."""

    filter: ImageAliasFilterInputDTO | None = Field(default=None, description="Filter conditions.")
    order: list[ImageAliasOrderByInputDTO] | None = Field(
        default=None, description="Order specifications."
    )
    first: int | None = Field(default=None, description="Cursor pagination: number of items.")
    after: str | None = Field(default=None, description="Cursor pagination: after cursor.")
    last: int | None = Field(default=None, description="Cursor pagination: last N items.")
    before: str | None = Field(default=None, description="Cursor pagination: before cursor.")
    limit: int | None = Field(default=None, description="Offset pagination: maximum items.")
    offset: int | None = Field(default=None, description="Offset pagination: number to skip.")


class UpdateImageInput(BaseRequestModel):
    """Input for updating an image by ID. All fields optional -- only provided fields will be updated."""

    image_id: UUID = Field(description="ID of the image to update.")
    name: str | None = Field(default=None, description="Updated canonical name.")
    registry: str | None = Field(default=None, description="Updated registry hostname.")
    image: str | None = Field(default=None, description="Updated namespace/path within registry.")
    tag: str | None = Field(default=None, description="Updated image tag.")
    architecture: str | None = Field(default=None, description="Updated CPU architecture.")
    is_local: bool | None = Field(default=None, description="Updated local-only status.")
    size_bytes: int | None = Field(default=None, description="Updated image size in bytes.")
    type: str | None = Field(
        default=None, description="Updated image type (compute, system, service)."
    )
    config_digest: str | None = Field(default=None, description="Updated config digest.")
    labels: dict[str, str] | None = Field(default=None, description="Updated labels dict.")
    supported_accelerators: str | Sentinel | None = Field(
        default=SENTINEL, description="Updated accelerator string. Set to null to clear."
    )
    resource_limits: dict[str, Any] | None = Field(
        default=None, description="Updated resource limits dict."
    )
