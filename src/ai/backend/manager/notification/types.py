"""Data types for notification system."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from ai.backend.common.data.notification import NotifiableMessage, NotificationRuleType

if TYPE_CHECKING:
    from ai.backend.manager.data.notification import NotificationChannelData

__all__ = (
    "NotificationMessage",
    "ProcessRuleParams",
    "SendResult",
)


@dataclass(frozen=True)
class NotificationMessage:
    """Notification message to be sent through a channel."""

    message: str


@dataclass(frozen=True)
class ProcessRuleParams:
    """Parameters for processing a notification rule."""

    message_template: str
    rule_type: NotificationRuleType
    channel: NotificationChannelData
    timestamp: datetime
    notification_data: NotifiableMessage


@dataclass(frozen=True)
class SendResult:
    """Result of sending a notification."""

    message: str
