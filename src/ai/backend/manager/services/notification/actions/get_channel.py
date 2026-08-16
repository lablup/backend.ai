from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.notification import (
    NOTIFICATION_CHANNEL_ENTITY_TYPE,
    NotificationChannelID,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GetGlobalOpsAction
from ai.backend.manager.data.notification.types import NotificationChannelData
from ai.backend.manager.models.notification.row import NotificationChannelRow
from ai.backend.manager.repositories.notification.queriers import NotificationChannelQuerier


@dataclass
class GetChannelAction(GetGlobalOpsAction[NotificationChannelRow, NotificationChannelData]):
    """Read one notification channel."""

    channel_id: NotificationChannelID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return NOTIFICATION_CHANNEL_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_notification_channel"

    @override
    def to_querier(self) -> NotificationChannelQuerier:
        return NotificationChannelQuerier(channel_id=self.channel_id)
