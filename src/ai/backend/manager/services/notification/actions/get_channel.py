from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.notification import NotificationChannelData
from ai.backend.manager.data.permission.types import RBACElementRef

from .base import NotificationChannelSingleEntityAction, NotificationChannelSingleEntityActionResult


@dataclass
class GetChannelAction(NotificationChannelSingleEntityAction):
    """Action to get a notification channel by ID."""

    channel_id: UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def target_entity_id(self) -> str:
        return str(self.channel_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.NOTIFICATION_CHANNEL, str(self.channel_id))


@dataclass
class GetChannelActionResult(NotificationChannelSingleEntityActionResult):
    """Result of getting a notification channel."""

    channel_data: NotificationChannelData

    @override
    def target_entity_id(self) -> str:
        return str(self.channel_data.id)
