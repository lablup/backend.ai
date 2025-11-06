from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.notification import NotificationRuleCreator, NotificationRuleData

from .base import NotificationAction


@dataclass
class CreateRuleAction(NotificationAction):
    """Action to create a notification rule."""

    creator: NotificationRuleCreator

    @override
    def entity_id(self) -> Optional[str]:
        return self.creator.name


@dataclass
class CreateRuleActionResult(BaseActionResult):
    """Result of creating a notification rule."""

    rule_data: NotificationRuleData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.rule_data.id)
