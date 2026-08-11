from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.notification import NOTIFICATION_RULE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.notification.types import NotificationRuleData
from ai.backend.manager.models.notification.row import NotificationRuleRow
from ai.backend.manager.repositories.notification.searchers import NotificationRuleSearcher


@dataclass
class SearchRulesAction(SearchGlobalOpsAction[NotificationRuleRow, NotificationRuleData]):
    """Page through the notification rules."""

    searcher: NotificationRuleSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return NOTIFICATION_RULE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_notification_rules"

    @override
    def to_searcher(self) -> NotificationRuleSearcher:
        return self.searcher
