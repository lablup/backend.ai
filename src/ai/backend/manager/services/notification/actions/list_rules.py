from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.notification import NotificationRuleEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.notification.types import NotificationRuleData
from ai.backend.manager.models.notification.row import NotificationRuleRow


@dataclass(frozen=True)
class SearchRulesAction(GlobalSearcherOpsAction[NotificationRuleRow, NotificationRuleData]):
    """Page through the notification rules."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return NotificationRuleEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_notification_rules"
