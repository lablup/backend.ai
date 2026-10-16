from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.notification import NotificationChannelID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeEntityOpsAction
from ai.backend.manager.data.notification.types import NotificationChannelData
from ai.backend.manager.models.notification.purgers import NotificationChannelPurger
from ai.backend.manager.models.notification.row import NotificationChannelRow


@dataclass(frozen=True)
class PartialBulkPurgeChannelsAction(
    PartialBulkPurgeEntityOpsAction[NotificationChannelRow, NotificationChannelData]
):
    """Remove the named notification channels, answering for each one."""

    ids: Sequence[NotificationChannelID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_purge_notification_channels"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_purgers(self) -> Mapping[EntityIdentifier, NotificationChannelPurger]:
        return {
            channel_id: NotificationChannelPurger(channel_id=channel_id) for channel_id in self.ids
        }

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[channel_id for channel_id in self.ids if channel_id in allowed])
