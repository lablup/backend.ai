from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.notification import (
    NotificationChannelID,
)
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.notification.types import NotificationChannelData
from ai.backend.manager.models.notification.purgers import NotificationChannelPurger
from ai.backend.manager.models.notification.row import NotificationChannelRow


@dataclass
class PurgeChannelAction(PurgeEntityOpsAction[NotificationChannelRow, NotificationChannelData]):
    """Remove a notification channel.

    Purge-shaped: the table carries no lifecycle column."""

    channel_id: NotificationChannelID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_notification_channel"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.to_purger().entity_id()

    @override
    def to_purger(self) -> NotificationChannelPurger:
        return NotificationChannelPurger(channel_id=self.channel_id)
