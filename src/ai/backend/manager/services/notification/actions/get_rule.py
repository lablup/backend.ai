from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.notification import (
    NOTIFICATION_RULE_ENTITY_TYPE,
    NotificationRuleID,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GetGlobalOpsAction
from ai.backend.manager.data.notification.types import NotificationRuleData
from ai.backend.manager.models.notification.row import NotificationRuleRow
from ai.backend.manager.repositories.notification.queriers import NotificationRuleQuerier


@dataclass
class GetRuleAction(GetGlobalOpsAction[NotificationRuleRow, NotificationRuleData]):
    """Read one notification rule."""

    rule_id: NotificationRuleID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return NOTIFICATION_RULE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_notification_rule"

    @override
    def to_querier(self) -> NotificationRuleQuerier:
        return NotificationRuleQuerier(rule_id=self.rule_id)
