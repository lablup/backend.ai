from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import NotificationAction


@dataclass
class ValidateRuleAction(NotificationAction):
    """Action to validate a notification rule by rendering its template with test data."""

    rule_id: UUID
    notification_data: Mapping[str, Any]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str | None:
        return str(self.rule_id)


@dataclass
class ValidateRuleActionResult(BaseActionResult):
    """Result of validating a notification rule."""

    message: str

    @override
    def entity_id(self) -> str | None:
        return None
