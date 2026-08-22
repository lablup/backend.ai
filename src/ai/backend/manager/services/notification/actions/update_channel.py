from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdateSingleEntityOpsAction
from ai.backend.manager.data.notification.types import NotificationChannelData
from ai.backend.manager.models.notification.row import NotificationChannelRow
from ai.backend.manager.models.notification.updaters import NotificationChannelUpdater


@dataclass
class UpdateChannelAction(
    UpdateSingleEntityOpsAction[NotificationChannelRow, NotificationChannelData]
):
    """Retune one notification channel."""

    updater: NotificationChannelUpdater

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_notification_channel"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.updater.channel_id

    @override
    def to_updater(self) -> NotificationChannelUpdater:
        return self.updater
