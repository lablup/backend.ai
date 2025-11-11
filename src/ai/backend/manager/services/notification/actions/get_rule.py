from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.notification import NotificationRuleData

from .base import NotificationAction


@dataclass
class GetRuleAction(NotificationAction):
    """Action to get a notification rule by ID."""

    rule_id: UUID

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_rule"

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.rule_id)


@dataclass
class GetRuleActionResult(BaseActionResult):
    """Result of getting a notification rule."""

    rule_data: NotificationRuleData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.rule_data.id)
