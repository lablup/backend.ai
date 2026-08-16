from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, override

from ai.backend.common.data.entity.notification import (
    NOTIFICATION_RULE_ENTITY_TYPE,
    NotificationRuleID,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass
class ValidateRuleAction(BaseGlobalAction):
    """Action to validate a notification rule by rendering its template with test data."""

    rule_id: NotificationRuleID
    notification_data: Mapping[str, Any]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return NOTIFICATION_RULE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "validate_notification_rule"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class ValidateRuleActionResult(BaseActionResult):
    """Result of validating a notification rule."""

    message: str

    @override
    def entity_id(self) -> str | None:
        return None
