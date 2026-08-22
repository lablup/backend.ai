from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdateSingleEntityOpsAction
from ai.backend.manager.data.notification.types import NotificationRuleData
from ai.backend.manager.models.notification.row import NotificationRuleRow
from ai.backend.manager.models.notification.updaters import NotificationRuleUpdater


@dataclass
class UpdateRuleAction(UpdateSingleEntityOpsAction[NotificationRuleRow, NotificationRuleData]):
    """Retune one notification rule."""

    updater: NotificationRuleUpdater

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_notification_rule"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.rule_id

    @override
    def to_updater(self) -> NotificationRuleUpdater:
        return self.updater
