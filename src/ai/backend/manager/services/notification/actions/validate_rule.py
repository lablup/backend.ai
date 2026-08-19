from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.notification import NotificationRuleID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


@dataclass
class ValidateRuleAction(BaseSingleEntityAction):
    """Action to validate a notification rule by rendering its template with test data."""

    rule_id: NotificationRuleID
    notification_data: Mapping[str, Any]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "validate_notification_rule"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.rule_id


@dataclass
class ValidateRuleActionResult:
    """Result of validating a notification rule."""

    message: str
