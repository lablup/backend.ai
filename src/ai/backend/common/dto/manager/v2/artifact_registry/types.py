"""
Common types for artifact registry DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel
from ai.backend.common.data.artifact.types import ArtifactRegistryType
from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "ArtifactOrderingField",
    "ArtifactRegistryType",
    "ArtifactRevisionReadmeInfo",
    "OrderDirection",
)


class ArtifactOrderingField(StrEnum):
    """Fields available for ordering artifacts."""

    NAME = "NAME"
    TYPE = "TYPE"
    SIZE = "SIZE"
    SCANNED_AT = "SCANNED_AT"
    UPDATED_AT = "UPDATED_AT"


class ArtifactRevisionReadmeInfo(BaseResponseModel):
    """Readme information for an artifact revision."""

    readme: str | None = Field(default=None, description="README content for the artifact revision")
