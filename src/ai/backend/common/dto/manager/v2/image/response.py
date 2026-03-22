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
    ImageResourceLimitGQLInfo,
    ImageResourceLimitInfo,
    ImageStatusType,
    ImageTagInfo,
    ImageTypeEnum,
)

__all__ = (
    "AdminSearchImageAliasesPayload",
    "AdminSearchImagesPayload",
    "AliasImagePayload",
    "ForgetImagePayload",
    "GetImagePayload",
    "ImageAliasNode",
    "ImageIdentityInfoDTO",
    "ImageMetadataInfoDTO",
    "ImageNode",
    "ImagePermissionInfoDTO",
    "ImageRequirementsInfoDTO",
    "PurgeImagePayload",
    "RescanImagesPayload",
    "SearchImagesPayload",
)


class ImageNode(BaseResponseModel):
    """Node model representing an image entity with full details."""

    id: UUID = Field(description="Image ID")
    name: str = Field(description="Image canonical name")
    image: str = Field(
        description="Image namespace/path within the registry (e.g. 'stable/python')"
    )
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
    identity: ImageIdentityInfoDTO | None = Field(
        default=None, description="Identity information (name, architecture)."
    )
    metadata: ImageMetadataInfoDTO | None = Field(
        default=None, description="Metadata information (labels, digest, size, status)."
    )
    requirements: ImageRequirementsInfoDTO | None = Field(
        default=None, description="Runtime requirements (accelerators, resource limits)."
    )


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


class ImageAliasNode(BaseResponseModel):
    """Node representing a single image alias."""

    id: UUID = Field(description="Alias ID.")
    alias: str = Field(description="Alias string.")


class AdminSearchImageAliasesPayload(BaseResponseModel):
    """Payload for admin-scoped paginated image alias search results."""

    items: list[ImageAliasNode] = Field(description="List of image alias nodes.")
    total_count: int = Field(description="Total number of aliases matching the filter.")
    has_next_page: bool = Field(description="Whether there is a next page.")
    has_previous_page: bool = Field(description="Whether there is a previous page.")


class ImageIdentityInfoDTO(BaseResponseModel):
    """DTO for ImageV2IdentityInfoGQL: identity information for an image."""

    canonical_name: str = Field(description="Full canonical name of the image.")
    namespace: str = Field(description="Image namespace/path within the registry.")
    architecture: str = Field(description="CPU architecture.")


class ImageMetadataInfoDTO(BaseResponseModel):
    """DTO for ImageV2MetadataInfoGQL: metadata information for an image."""

    digest: str | None = Field(default=None, description="Config digest for verification.")
    size_bytes: int = Field(description="Image size in bytes.")
    created_at: datetime | None = Field(default=None, description="Image creation timestamp.")
    tags: list[ImageTagInfo] = Field(default_factory=list, description="Parsed tag components.")
    labels: list[ImageLabelInfo] = Field(default_factory=list, description="Docker labels.")
    status: ImageStatusType = Field(description="Image status (ALIVE or DELETED).")


class ImageRequirementsInfoDTO(BaseResponseModel):
    """DTO for ImageV2RequirementsInfoGQL: runtime requirements for an image."""

    supported_accelerators: list[str] = Field(
        default_factory=list, description="List of supported accelerator types."
    )
    resource_limits: list[ImageResourceLimitGQLInfo] = Field(
        default_factory=list, description="Resource slot limits with string min/max values."
    )


class ImagePermissionInfoDTO(BaseResponseModel):
    """DTO for ImageV2PermissionInfoGQL: permission information for an image."""

    permissions: list[str] = Field(description="List of permissions the user has on this image")
