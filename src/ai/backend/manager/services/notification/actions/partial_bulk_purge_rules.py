from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.notification import NotificationRuleID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeEntityOpsAction
from ai.backend.manager.data.notification.types import NotificationRuleData
from ai.backend.manager.models.notification.purgers import NotificationRulePurger
from ai.backend.manager.models.notification.row import NotificationRuleRow


@dataclass(frozen=True)
class PartialBulkPurgeRulesAction(
    PartialBulkPurgeEntityOpsAction[NotificationRuleRow, NotificationRuleData]
):
    """Remove the named notification rules, answering for each one."""

    ids: Sequence[NotificationRuleID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_purge_notification_rules"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_purgers(self) -> Mapping[EntityIdentifier, NotificationRulePurger]:
        return {rule_id: NotificationRulePurger(rule_id=rule_id) for rule_id in self.ids}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[rule_id for rule_id in self.ids if rule_id in allowed])
