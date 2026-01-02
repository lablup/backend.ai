from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, cast

from typing_extensions import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.notification import NotificationRuleData
from ai.backend.manager.repositories.base import Creator
from ai.backend.manager.repositories.notification.creators import NotificationRuleCreatorSpec

from .base import NotificationAction

if TYPE_CHECKING:
    from ai.backend.manager.models.notification import NotificationRuleRow


@dataclass
class CreateRuleAction(NotificationAction):
    """Action to create a notification rule."""

    creator: Creator[NotificationRuleRow]

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create_rule"

    @override
    def entity_id(self) -> Optional[str]:
        spec = cast(NotificationRuleCreatorSpec, self.creator.spec)
        return spec.name


@dataclass
class CreateRuleActionResult(BaseActionResult):
    """Result of creating a notification rule."""

    rule_data: NotificationRuleData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.rule_data.id)
