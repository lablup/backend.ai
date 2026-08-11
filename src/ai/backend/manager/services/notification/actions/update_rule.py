from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.notification import NOTIFICATION_RULE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import UpdateGlobalOpsAction
from ai.backend.manager.data.notification.types import NotificationRuleData
from ai.backend.manager.models.notification.row import NotificationRuleRow
from ai.backend.manager.repositories.notification.updaters import NotificationRuleUpdater


@dataclass
class UpdateRuleAction(UpdateGlobalOpsAction[NotificationRuleRow, NotificationRuleData]):
    """Retune one notification rule."""

    updater: NotificationRuleUpdater

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return NOTIFICATION_RULE_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_notification_rule"

    @override
    def to_updater(self) -> NotificationRuleUpdater:
        return self.updater
