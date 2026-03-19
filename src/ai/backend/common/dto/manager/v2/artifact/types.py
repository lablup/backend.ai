"""
Common types for artifact DTO v2.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel, BaseResponseModel
from ai.backend.common.data.artifact.types import (
    ArtifactRegistryType,
    CombinedDownloadProgress,
    VerificationStepResult,
)

__all__ = (
    "ArtifactAvailability",
    "ArtifactAvailabilityFilter",
    "ArtifactOrderField",
    "ArtifactRegistryType",
    "ArtifactRemoteStatus",
    "ArtifactRevisionInfo",
    "ArtifactRevisionOrderField",
    "ArtifactStatus",
    "ArtifactType",
    "ArtifactTypeFilter",
    "CombinedDownloadProgress",
    "OrderDirection",
    "VerificationStepResult",
)


class ArtifactType(StrEnum):
    """Type of artifact."""

    MODEL = "MODEL"
    PACKAGE = "PACKAGE"
    IMAGE = "IMAGE"


class ArtifactStatus(StrEnum):
    """Status of an artifact revision."""

    SCANNED = "SCANNED"
    PULLING = "PULLING"
    PULLED = "PULLED"
    VERIFYING = "VERIFYING"
    NEEDS_APPROVAL = "NEEDS_APPROVAL"
    AVAILABLE = "AVAILABLE"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


class ArtifactRemoteStatus(StrEnum):
    """Remote status of an artifact revision."""

    SCANNED = "SCANNED"
    AVAILABLE = "AVAILABLE"
    FAILED = "FAILED"


class ArtifactAvailability(StrEnum):
    """Availability of an artifact."""

    ALIVE = "ALIVE"
    DELETED = "DELETED"


class ArtifactOrderField(StrEnum):
    """Fields available for ordering artifacts."""

    NAME = "NAME"
    TYPE = "TYPE"
    SIZE = "SIZE"
    SCANNED_AT = "SCANNED_AT"
    UPDATED_AT = "UPDATED_AT"


class ArtifactRevisionOrderField(StrEnum):
    """Fields available for ordering artifact revisions."""

    VERSION = "VERSION"
    SIZE = "SIZE"
    CREATED_AT = "CREATED_AT"
    UPDATED_AT = "UPDATED_AT"
    STATUS = "STATUS"


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class ArtifactTypeFilter(BaseRequestModel):
    """Filter for artifact type enum fields."""

    equals: ArtifactType | None = Field(default=None, description="Exact match for artifact type.")
    in_: list[ArtifactType] | None = Field(
        default=None, alias="in", description="Match any of the provided types."
    )
    not_equals: ArtifactType | None = Field(default=None, description="Exclude exact type match.")
    not_in: list[ArtifactType] | None = Field(
        default=None, description="Exclude any of the provided types."
    )


class ArtifactAvailabilityFilter(BaseRequestModel):
    """Filter for artifact availability enum fields."""

    equals: ArtifactAvailability | None = Field(
        default=None, description="Exact match for availability."
    )
    in_: list[ArtifactAvailability] | None = Field(
        default=None, alias="in", description="Match any of the provided availability values."
    )
    not_equals: ArtifactAvailability | None = Field(
        default=None, description="Exclude exact availability match."
    )
    not_in: list[ArtifactAvailability] | None = Field(
        default=None, description="Exclude any of the provided availability values."
    )


class ArtifactRevisionInfo(BaseResponseModel):
    """Compact revision view for embedding inside ArtifactNode."""

    id: UUID = Field(description="Artifact revision ID")
    version: str = Field(description="Revision version string")
    size: int | None = Field(default=None, description="Revision size in bytes")
    status: ArtifactStatus = Field(description="Revision status")
    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")
