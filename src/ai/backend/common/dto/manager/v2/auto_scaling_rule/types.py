"""
Common types for auto-scaling rule DTO v2.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.types import AutoScalingMetricSource

__all__ = (
    "AutoScalingMetricSource",
    "AutoScalingRuleOrderField",
    "OrderDirection",
)


class AutoScalingRuleOrderField(StrEnum):
    """Fields available for ordering auto-scaling rules."""

    CREATED_AT = "created_at"
