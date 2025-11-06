from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.notification import NotificationRuleData
from ai.backend.manager.repositories.base import Querier

from .base import NotificationAction


@dataclass
class ListRulesAction(NotificationAction):
    """Action to list notification rules."""

    querier: Optional[Querier] = None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "list_rules"

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class ListRulesActionResult(BaseActionResult):
    """Result of listing notification rules."""

    rules: list[NotificationRuleData]

    @override
    def entity_id(self) -> Optional[str]:
        return None
