from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdatePartialBulkOpsAction
from ai.backend.manager.data.notification.types import NotificationChannelData
from ai.backend.manager.models.notification.row import NotificationChannelRow
from ai.backend.manager.models.notification.updaters import NotificationChannelUpdater


@dataclass(frozen=True)
class PartialBulkUpdateChannelsAction(
    UpdatePartialBulkOpsAction[NotificationChannelRow, NotificationChannelData]
):
    """Retune the named notification channels, answering for each one."""

    updaters: Sequence[NotificationChannelUpdater]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_update_notification_channels"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(updater.channel_id for updater in self.updaters)

    @override
    def to_updaters(self) -> Mapping[EntityIdentifier, NotificationChannelUpdater]:
        return {updater.channel_id: updater for updater in self.updaters}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self, updaters=[updater for updater in self.updaters if updater.channel_id in allowed]
        )
