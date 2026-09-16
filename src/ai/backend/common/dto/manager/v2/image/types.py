"""
Common types for image DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel, BaseResponseModel
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.rbac.types import UUIDScope

__all__ = (
    "ImageLabelInfo",
    "ImageScope",
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


class ImageScope(BaseRequestModel):
    """Scope for the scoped image query.

    Each list is OR'd internally and across lists. ``global_`` names no scope and is
    authorized against none: a registry marked global shows its images to everyone.
    Raises an error if every field is empty.
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
