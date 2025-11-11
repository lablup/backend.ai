from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult

from .base import NotificationAction


@dataclass
class DeleteRuleAction(NotificationAction):
    """Action to delete a notification rule."""

    rule_id: UUID

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete_rule"

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.rule_id)


@dataclass
class DeleteRuleActionResult(BaseActionResult):
    """Result of deleting a notification rule."""

    deleted: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
