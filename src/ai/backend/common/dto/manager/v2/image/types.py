"""
Common types for image DTO v2.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from ai.backend.common.api_handlers import BaseResponseModel

__all__ = (
    "ImageLabelInfo",
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


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


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
    min: Decimal
    max: Decimal | None


class ImageResourceLimitGQLInfo(BaseResponseModel):
    """Resource limit definition for GQL type (min/max as str for display)."""

    key: str
    min: str
    max: str


class ImagePermissionType(BaseResponseModel):
    """A single permission entry for an image."""

    value: str
