from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdatePartialBulkOpsAction
from ai.backend.manager.data.notification.types import NotificationRuleData
from ai.backend.manager.models.notification.row import NotificationRuleRow
from ai.backend.manager.models.notification.updaters import NotificationRuleUpdater


@dataclass(frozen=True)
class PartialBulkUpdateRulesAction(
    UpdatePartialBulkOpsAction[NotificationRuleRow, NotificationRuleData]
):
    """Retune the named notification rules, answering for each one."""

    updaters: Sequence[NotificationRuleUpdater]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_update_notification_rules"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(updater.rule_id for updater in self.updaters)

    @override
    def to_updaters(self) -> Mapping[EntityIdentifier, NotificationRuleUpdater]:
        return {updater.rule_id: updater for updater in self.updaters}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self, updaters=[updater for updater in self.updaters if updater.rule_id in allowed]
        )
