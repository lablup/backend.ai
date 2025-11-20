from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.notification import NotificationRuleData
from ai.backend.manager.repositories.base import Querier

from .base import NotificationAction


@dataclass
class SearchRulesAction(NotificationAction):
    """Action to search notification rules."""

    querier: Optional[Querier] = None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search_rules"

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class SearchRulesActionResult(BaseActionResult):
    """Result of searching notification rules."""

    rules: list[NotificationRuleData]
    total_count: int

    @override
    def entity_id(self) -> Optional[str]:
        return None
