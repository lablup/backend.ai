"""
Request DTOs for image DTO v2.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field, field_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.defs import DEFAULT_PAGE_LIMIT
from ai.backend.common.dto.manager.query import (
    DateTimeFilter,
    EnumFilter,
    IntFilter,
    StringFilter,
    UUIDFilter,
)
from ai.backend.common.tristate.unset import UNSET, Unset

from .types import (
    ImageAliasOrderField,
    ImageOrderField,
    ImageScope,
    ImageStatusType,
    ImageTypeEnum,
    ImageUsage,
    OrderDirection,
)

__all__ = (
    "AdminSearchImageAliasesInput",
    "AdminSearchImagesInput",
    "AliasImageInput",
    "ContainerRegistryScopeInputDTO",
    "DealiasImageInput",
    "ForgetImageInput",
    "RestoreImageInput",
    "ImageAliasFilterInputDTO",
    "ImageAliasNestedFilterInputDTO",
    "ImageAliasOrderByInputDTO",
    "ImageFilter",
    "ImageFilterInputDTO",
    "ImageOrder",
    "ImageOrderByInputDTO",
    "ImageScopeInputDTO",
    "ImageStatusFilterInputDTO",
    "ImageTypeFilterInputDTO",
    "ImageUsage",
    "PurgeImageInput",
    "RescanImagesInput",
    "ScopedSearchImagesInput",
    "SearchImageAliasesInput",
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


class ImageStatusFilterInputDTO(EnumFilter[ImageStatusType]):
    """Filter for image status."""


class ImageTypeFilterInputDTO(EnumFilter[ImageTypeEnum]):
    """Filter for the image type category."""


class ImageAliasNestedFilterInputDTO(BaseRequestModel):
    """Nested filter for image aliases within an image."""

    alias: StringFilter | None = Field(default=None, description="Filter by alias string.")


class ImageFilterInputDTO(BaseRequestModel):
    """Filter options for images."""

    id: UUIDFilter | None = Field(default=None, description="Filter by image UUID.")
    status: ImageStatusFilterInputDTO | None = Field(default=None, description="Filter by status.")
    name: StringFilter | None = Field(default=None, description="Filter by name.")
    architecture: StringFilter | None = Field(default=None, description="Filter by architecture.")
    registry_id: UUIDFilter | None = Field(
        default=None, description="Filter by container registry ID."
    )
    image: StringFilter | None = Field(
        default=None, description="Filter by namespace/path within the registry."
    )
    registry: StringFilter | None = Field(default=None, description="Filter by registry hostname.")
    project: StringFilter | None = Field(
        default=None, description="Filter by project (namespace) within the registry."
    )
    tag: StringFilter | None = Field(default=None, description="Filter by image tag.")
    config_digest: StringFilter | None = Field(
        default=None, description="Filter by image config digest."
    )
    accelerators: StringFilter | None = Field(
        default=None, description="Filter by accelerator requirement string."
    )
    size_bytes: IntFilter | None = Field(default=None, description="Filter by image size in bytes.")
    is_local: bool | None = Field(default=None, description="Filter by local-only status.")
    type: ImageTypeFilterInputDTO | None = Field(
        default=None, description="Filter by image type category."
    )
    created_at: DateTimeFilter | None = Field(
        default=None, description="Filter by creation datetime (before/after)."
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
    field_id: UUIDFilter | None = Field(default=None, description="Filter by alias row ID.")
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

    field: ImageAliasOrderField = Field(description="Field to order by.")
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
    limit: int = Field(
        default=DEFAULT_PAGE_LIMIT, ge=1, le=1000, description="Maximum items to return"
    )
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


class RestoreImageInput(BaseRequestModel):
    """Input for restoring a forgotten (soft-deleted) image."""

    image_id: UUID = Field(description="ID of the image to restore")


class PurgeImageInput(BaseRequestModel):
    """Input for purging (hard-deleting) an image."""

    image_id: UUID = Field(description="ID of the image to purge")


class AdminSearchImagesInput(BaseRequestModel):
    """Input for admin search of images with cursor and offset pagination."""

    usage: ImageUsage | None = Field(
        default=None,
        description=(
            "Uses narrowing the result. Each listed entity must be readable by the caller; "
            "images the caller cannot read are left out."
        ),
    )
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


class ScopedSearchImagesInput(BaseRequestModel):
    """Input for searching the images the named scopes reach."""

    scope: ImageScope = Field(description="Scope (OR across all items).")
    usage: ImageUsage | None = Field(
        default=None,
        description=(
            "Uses narrowing the result. Each listed entity must be readable by the caller; "
            "images the caller cannot read are left out."
        ),
    )
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


class SearchImageAliasesInput(BaseRequestModel):
    """Input for searching the aliases of one image with cursor and offset pagination."""

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
    name: str | None | Unset = Field(
        default=UNSET, description="Updated canonical name. Omit to leave unchanged."
    )
    registry: str | None | Unset = Field(
        default=UNSET, description="Updated registry hostname. Omit to leave unchanged."
    )
    image: str | None | Unset = Field(
        default=UNSET,
        description="Updated namespace/path within registry. Omit to leave unchanged.",
    )
    tag: str | None | Unset = Field(
        default=UNSET, description="Updated image tag. Omit to leave unchanged."
    )
    architecture: str | None | Unset = Field(
        default=UNSET, description="Updated CPU architecture. Omit to leave unchanged."
    )
    is_local: bool | None | Unset = Field(
        default=UNSET, description="Updated local-only status. Omit to leave unchanged."
    )
    size_bytes: int | None | Unset = Field(
        default=UNSET, description="Updated image size in bytes. Omit to leave unchanged."
    )
    type: str | None | Unset = Field(
        default=UNSET,
        description="Updated image type (compute, system, service). Omit to leave unchanged.",
    )
    config_digest: str | None | Unset = Field(
        default=UNSET, description="Updated config digest. Omit to leave unchanged."
    )
    labels: dict[str, str] | None | Unset = Field(
        default=UNSET, description="Updated labels dict. Omit to leave unchanged."
    )
    supported_accelerators: str | None | Unset = Field(
        default=UNSET,
        description="Updated accelerator string. Omit to leave unchanged; null clears.",
    )
    resource_limits: dict[str, Any] | None | Unset = Field(
        default=UNSET, description="Updated resource limits dict. Omit to leave unchanged."
    )
