"""
Shared types for Prometheus Query Preset DTOs.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from ai.backend.common.api_handlers import BaseRequestModel

__all__ = (
    "OrderDirection",
    "PresetOrderField",
    "PresetOrder",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class PresetOrderField(StrEnum):
    """Fields available for ordering prometheus query presets."""

    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class PresetOrder(BaseRequestModel):
    """Order specification for prometheus query presets."""

    field: PresetOrderField = Field(description="Field to order by")
    direction: OrderDirection = Field(default=OrderDirection.ASC, description="Order direction")
