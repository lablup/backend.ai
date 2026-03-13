from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.notification import NotificationChannelData
from ai.backend.manager.data.permission.types import RBACElementRef
from ai.backend.manager.models.notification import NotificationChannelRow
from ai.backend.manager.repositories.base.updater import Updater

from .base import NotificationChannelSingleEntityAction, NotificationChannelSingleEntityActionResult


@dataclass
class UpdateChannelAction(NotificationChannelSingleEntityAction):
    """Action to update a notification channel."""

    updater: Updater[NotificationChannelRow]

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def target_entity_id(self) -> str:
        return str(self.updater.pk_value)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.NOTIFICATION_CHANNEL, str(self.updater.pk_value))


@dataclass
class UpdateChannelActionResult(NotificationChannelSingleEntityActionResult):
    """Result of updating a notification channel."""

    channel_data: NotificationChannelData

    @override
    def target_entity_id(self) -> str:
        return str(self.channel_data.id)
