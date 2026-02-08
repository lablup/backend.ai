from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.notification import NotificationRuleData

from .base import NotificationAction


@dataclass
class GetRuleAction(NotificationAction):
    """Action to get a notification rule by ID."""

    rule_id: UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return str(self.rule_id)


@dataclass
class GetRuleActionResult(BaseActionResult):
    """Result of getting a notification rule."""

    rule_data: NotificationRuleData

    @override
    def entity_id(self) -> str | None:
        return str(self.rule_data.id)
