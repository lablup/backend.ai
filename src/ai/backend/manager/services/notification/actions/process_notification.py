from dataclasses import dataclass
from datetime import datetime
from typing import Optional, override
from uuid import UUID

from ai.backend.common.data.notification import NotifiableMessage, NotificationRuleType
from ai.backend.manager.actions.action import BaseActionResult

from .base import NotificationAction


@dataclass
class ProcessedRuleSuccess:
    """Information about a successfully processed notification rule."""

    rule_id: UUID
    rule_name: str
    channel_name: str


@dataclass
class ProcessNotificationAction(NotificationAction):
    """Action to process a notification event."""

    rule_type: NotificationRuleType
    timestamp: datetime
    notification_data: NotifiableMessage

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.rule_type)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "process_notification"


@dataclass
class ProcessNotificationActionResult(BaseActionResult):
    """Result of processing a notification."""

    rule_type: NotificationRuleType
    rules_matched: int
    successes: list[ProcessedRuleSuccess]
    errors: list[BaseException]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.rule_type)
