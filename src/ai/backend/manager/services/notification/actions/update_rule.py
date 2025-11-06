from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.notification import NotificationRuleData, NotificationRuleModifier

from .base import NotificationAction


@dataclass
class UpdateRuleAction(NotificationAction):
    """Action to update a notification rule."""

    rule_id: UUID
    modifier: NotificationRuleModifier

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "update_rule"

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.rule_id)


@dataclass
class UpdateRuleActionResult(BaseActionResult):
    """Result of updating a notification rule."""

    rule_data: NotificationRuleData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.rule_data.id)
