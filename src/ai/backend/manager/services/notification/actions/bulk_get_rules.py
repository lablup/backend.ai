from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.notification import NotificationRuleID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.notification.types import NotificationRuleData
from ai.backend.manager.models.notification.queriers import BulkNotificationRuleQuerier
from ai.backend.manager.models.notification.row import NotificationRuleRow


@dataclass
class BulkGetRulesAction(PartialBulkGetEntityOpsAction[NotificationRuleRow, NotificationRuleData]):
    """Read the notification rules the caller named, answering for each id."""

    ids: Sequence[NotificationRuleID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_notification_rules"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkNotificationRuleQuerier:
        return BulkNotificationRuleQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
