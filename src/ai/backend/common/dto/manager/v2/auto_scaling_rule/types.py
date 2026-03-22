"""
Common types for auto-scaling rule DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.types import AutoScalingMetricSource

__all__ = (
    "AutoScalingMetricSource",
    "AutoScalingRuleOrderField",
    "OrderDirection",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class AutoScalingRuleOrderField(StrEnum):
    """Fields available for ordering auto-scaling rules."""

    CREATED_AT = "created_at"
