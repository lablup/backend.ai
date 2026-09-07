from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.notification import NotificationChannelID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkGetEntityOpsAction
from ai.backend.manager.data.notification.types import NotificationChannelData
from ai.backend.manager.models.notification.queriers import BulkNotificationChannelQuerier
from ai.backend.manager.models.notification.row import NotificationChannelRow


@dataclass
class BulkGetChannelsAction(
    PartialBulkGetEntityOpsAction[NotificationChannelRow, NotificationChannelData]
):
    """Read the notification channels the caller named, answering for each id."""

    ids: Sequence[NotificationChannelID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "bulk_get_notification_channels"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_querier(self) -> BulkNotificationChannelQuerier:
        return BulkNotificationChannelQuerier()

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[entity_id for entity_id in self.ids if entity_id in allowed])
