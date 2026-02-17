"""
Common types for auto-scaling rule system.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = (
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
