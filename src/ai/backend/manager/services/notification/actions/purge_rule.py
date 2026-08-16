from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.notification import NOTIFICATION_RULE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.notification import NotificationRuleID
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.notification.types import NotificationRuleData
from ai.backend.manager.models.notification.purgers import NotificationRulePurger
from ai.backend.manager.models.notification.row import NotificationRuleRow


@dataclass
class PurgeRuleAction(PurgeEntityOpsAction[NotificationRuleRow, NotificationRuleData]):
    """Remove a notification rule.

    Purge-shaped: the table carries no lifecycle column."""

    rule_id: NotificationRuleID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return NOTIFICATION_RULE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_notification_rule"

    @override
    def entity_id(self) -> EntityID:
        return self.to_purger().entity_id()

    @override
    def to_purger(self) -> NotificationRulePurger:
        return NotificationRulePurger(rule_id=self.rule_id)
