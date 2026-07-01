"""
Common types for prometheus_query_preset_category DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "OrderDirection",
    "CategoryOrderField",
)


class CategoryOrderField(StrEnum):
    """Fields available for ordering prometheus query preset categories."""

    NAME = "name"
    CREATED_AT = "created_at"
