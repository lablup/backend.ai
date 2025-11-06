"""
Common types for notification system.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

__all__ = (
    "NotificationChannelType",
    "NotificationRuleType",
    "WebhookConfig",
    "OrderDirection",
    "NotificationChannelOrderField",
    "NotificationRuleOrderField",
)


class NotificationChannelType(StrEnum):
    """Notification channel types."""

    WEBHOOK = "webhook"


class NotificationRuleType(StrEnum):
    """Notification rule types."""

    SESSION_STARTED = "session.started"
    SESSION_TERMINATED = "session.terminated"
    ARTIFACT_DOWNLOAD_COMPLETED = "artifact.download.completed"


class WebhookConfig(BaseModel):
    """Configuration for webhook notification channel."""

    url: str = Field(description="Webhook URL")


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
