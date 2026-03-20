"""Common types for Resource Usage DTO v2."""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.common import OrderDirection

__all__ = (
    "OrderDirection",
    "UsageBucketOrderField",
)


class UsageBucketOrderField(StrEnum):
    """Fields available for ordering usage buckets."""

    PERIOD_START = "period_start"
