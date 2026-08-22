from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.notification import NOTIFICATION_CHANNEL_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import CreateGlobalOpsAction
from ai.backend.manager.data.notification.types import NotificationChannelData
from ai.backend.manager.models.notification.creators import NotificationChannelCreator
from ai.backend.manager.models.notification.row import NotificationChannelRow


@dataclass
class CreateChannelAction(CreateGlobalOpsAction[NotificationChannelRow, NotificationChannelData]):
    """Register a notification channel."""

    creator: NotificationChannelCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return NOTIFICATION_CHANNEL_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_notification_channel"

    @override
    def to_creator(self) -> NotificationChannelCreator:
        return self.creator
