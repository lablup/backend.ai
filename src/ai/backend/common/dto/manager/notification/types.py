"""
Common types for notification system.
"""

from __future__ import annotations

from enum import StrEnum

from ai.backend.common.data.notification import (
    NotificationChannelType,
    NotificationRuleType,
    WebhookConfig,
)

__all__ = (
    "NotificationChannelType",
    "NotificationRuleType",
    "WebhookConfig",
    "OrderDirection",
    "NotificationChannelOrderField",
    "NotificationRuleOrderField",
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
