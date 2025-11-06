from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.notification import NotificationRuleType

from .base import NotificationAction


@dataclass
class ProcessNotificationAction(NotificationAction):
    """Action to process a notification event."""

    rule_type: NotificationRuleType
    timestamp: datetime
    notification_data: Mapping[str, Any]

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
    rules_processed: int

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.rule_type)
