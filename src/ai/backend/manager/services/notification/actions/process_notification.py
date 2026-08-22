from dataclasses import dataclass
from datetime import datetime
from typing import override
from uuid import UUID

from ai.backend.common.data.entity.notification import NOTIFICATION_RULE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.data.notification import NotifiableMessage, NotificationRuleType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass
class ProcessedRuleSuccess:
    """Information about a successfully processed notification rule."""

    rule_id: UUID
    rule_name: str
    channel_name: str


@dataclass
class ProcessNotificationAction(BaseGlobalAction):
    """Action to process a notification event."""

    rule_type: NotificationRuleType
    timestamp: datetime
    notification_data: NotifiableMessage

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return NOTIFICATION_RULE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "process_notification"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class ProcessNotificationActionResult:
    """Result of processing a notification."""

    rule_type: NotificationRuleType
    rules_matched: int
    successes: list[ProcessedRuleSuccess]
    errors: list[BaseException]
