from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.notification import NOTIFICATION_CHANNEL_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import UpdateGlobalOpsAction
from ai.backend.manager.data.notification.types import NotificationChannelData
from ai.backend.manager.models.notification.row import NotificationChannelRow
from ai.backend.manager.repositories.notification.updaters import NotificationChannelUpdater


@dataclass
class UpdateChannelAction(UpdateGlobalOpsAction[NotificationChannelRow, NotificationChannelData]):
    """Retune one notification channel."""

    updater: NotificationChannelUpdater

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return NOTIFICATION_CHANNEL_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_notification_channel"

    @override
    def to_updater(self) -> NotificationChannelUpdater:
        return self.updater
