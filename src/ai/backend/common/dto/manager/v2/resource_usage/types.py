"""Common types for Resource Usage DTO v2."""

from __future__ import annotations

from enum import StrEnum

__all__ = (
    "OrderDirection",
    "UsageBucketOrderField",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class UsageBucketOrderField(StrEnum):
    """Fields available for ordering usage buckets."""

    PERIOD_START = "period_start"
