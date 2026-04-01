from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef

from .base import NotificationChannelSingleEntityAction, NotificationChannelSingleEntityActionResult


@dataclass
class DeleteChannelAction(NotificationChannelSingleEntityAction):
    """Action to delete a notification channel."""

    channel_id: UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def target_entity_id(self) -> str:
        return str(self.channel_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.NOTIFICATION_CHANNEL, str(self.channel_id))


@dataclass
class DeleteChannelActionResult(NotificationChannelSingleEntityActionResult):
    """Result of deleting a notification channel."""

    deleted: bool

    @override
    def target_entity_id(self) -> str:
        return ""
