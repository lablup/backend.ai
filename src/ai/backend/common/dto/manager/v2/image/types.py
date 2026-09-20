"""
Common types for image DTO v2.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel, BaseResponseModel
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope

__all__ = (
    "ImageAliasOrderField",
    "ImageLabelInfo",
    "ImageScope",
    "ImageUsedBy",
    "ImageOrderField",
    "ImagePermissionType",
    "ImageResourceLimitGQLInfo",
    "ImageResourceLimitInfo",
    "ImageStatusType",
    "ImageTagInfo",
    "ImageTypeEnum",
    "OrderDirection",
)


class ImageStatusType(StrEnum):
    """Status of an image."""

    ALIVE = "ALIVE"
    DELETED = "DELETED"


class ImageTypeEnum(StrEnum):
    """Type category of an image."""

    COMPUTE = "compute"
    SYSTEM = "system"
    SERVICE = "service"


class ImageOrderField(StrEnum):
    """Fields available for ordering images."""

    NAME = "name"
    CREATED_AT = "created_at"
    LAST_USED = "last_used"
    ENTITY_ID = "entity_id"
    IMAGE = "image"
    PROJECT = "project"
    TAG = "tag"
    REGISTRY = "registry"
    REGISTRY_ID = "registry_id"
    ARCHITECTURE = "architecture"
    CONFIG_DIGEST = "config_digest"
    SIZE_BYTES = "size_bytes"
    IS_LOCAL = "is_local"
    TYPE = "type"
    STATUS = "status"
    ACCELERATORS = "accelerators"


class ImageAliasOrderField(StrEnum):
    """Fields available for ordering image aliases."""

    ALIAS = "alias"
    FIELD_ID = "field_id"


class ImageTagInfo(BaseResponseModel):
    """A single key-value tag attached to an image."""

    key: str
    value: str


class ImageLabelInfo(BaseResponseModel):
    """A single key-value label attached to an image."""

    key: str
    value: str


class ImageResourceLimitInfo(BaseResponseModel):
    """Resource limit definition for a specific resource slot of an image."""

    key: str
    min: str
    max: str | None


class ImageResourceLimitGQLInfo(BaseResponseModel):
    """Resource limit definition for GQL type (min/max as str for display)."""

    key: str
    min: str
    max: str


class ImagePermissionType(BaseResponseModel):
    """A single permission entry for an image."""

    value: str


class ImageUsedBy(BaseRequestModel):
    """Entities whose use narrows the images read; every id is AND-ed.

    An entity the caller cannot read refuses the request. Images the caller cannot read
    are left out even when a listed entity uses them.
    """

    session: list[UUID] | None = Field(
        default=None, description="Sessions whose kernels run the image"
    )
    deployment: list[UUID] | None = Field(
        default=None,
        description="Deployments whose live replica groups name the image in their current revision",
    )


class ImageScope(BaseRequestModel):
    """Scope for the scoped image query.

    Each list is OR'd internally and across lists. ``global_`` is answered for at the
    public scope, which every account reaches: a registry marked global shows its images
    to everyone. Raises an error if every field is empty.
    """

    domain: list[UUIDScope] | None = Field(
        default=None, description="Domains whose images are being read"
    )
    project: list[UUIDScope] | None = Field(
        default=None, description="Projects whose images are being read"
    )
    user: list[UUIDScope] | None = Field(
        default=None, description="Users whose images are being read"
    )
    container_registry: list[UUIDScope] | None = Field(
        default=None, description="Container registries whose images are being read"
    )
    global_: bool = Field(
        default=False,
        alias="global",
        description="Include the images of every registry marked global",
    )

    @model_validator(mode="after")
    def _require_non_empty(self) -> ImageScope:
        if (
            not self.domain
            and not self.project
            and not self.user
            and not self.container_registry
            and not self.global_
        ):
            raise ValueError(
                "ImageScope requires a non-empty value for 'domain', 'project', 'user', "
                "'container_registry' or 'global'"
            )
        return self
