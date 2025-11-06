from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.notification import NotificationRuleData, NotificationRuleType

from .base import NotificationAction


@dataclass
class ListRulesAction(NotificationAction):
    """Action to list notification rules."""

    enabled_only: bool = False
    rule_type: Optional[NotificationRuleType] = None

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.rule_type) if self.rule_type else None


@dataclass
class ListRulesActionResult(BaseActionResult):
    """Result of listing notification rules."""

    rules: list[NotificationRuleData]

    @override
    def entity_id(self) -> Optional[str]:
        return None
