from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.notification import NotificationChannelID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import GetSingleEntityOpsAction
from ai.backend.manager.data.notification.types import NotificationChannelData
from ai.backend.manager.models.notification.queriers import NotificationChannelQuerier
from ai.backend.manager.models.notification.row import NotificationChannelRow


@dataclass
class GetChannelAction(GetSingleEntityOpsAction[NotificationChannelRow, NotificationChannelData]):
    """Read one notification channel."""

    channel_id: NotificationChannelID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_notification_channel"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.channel_id

    @override
    def to_querier(self) -> NotificationChannelQuerier:
        return NotificationChannelQuerier(channel_id=self.channel_id)
