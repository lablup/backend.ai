"""
Common types for notification system.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = (
    "NotificationChannelOrderField",
    "NotificationRuleOrderField",
    "OrderDirection",
)


class OrderDirection(StrEnum):
    """Order direction for sorting."""

    ASC = "asc"
    DESC = "desc"


class NotificationChannelOrderField(StrEnum):
    """Fields available for ordering notification channels."""

    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class NotificationRuleOrderField(StrEnum):
    """Fields available for ordering notification rules."""

    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
