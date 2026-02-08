from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import NotificationAction


@dataclass
class DeleteRuleAction(NotificationAction):
    """Action to delete a notification rule."""

    rule_id: UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def entity_id(self) -> str | None:
        return str(self.rule_id)


@dataclass
class DeleteRuleActionResult(BaseActionResult):
    """Result of deleting a notification rule."""

    deleted: bool

    @override
    def entity_id(self) -> str | None:
        return None
