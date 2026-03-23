from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.permission.types import RBACElementType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.permission.types import RBACElementRef

from .base import NotificationChannelSingleEntityAction, NotificationChannelSingleEntityActionResult


@dataclass
class ValidateChannelAction(NotificationChannelSingleEntityAction):
    """Action to validate a notification channel (webhook sending test)."""

    channel_id: UUID
    test_message: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def target_entity_id(self) -> str:
        return str(self.channel_id)

    @override
    def target_element(self) -> RBACElementRef:
        return RBACElementRef(RBACElementType.NOTIFICATION_CHANNEL, str(self.channel_id))


@dataclass
class ValidateChannelActionResult(NotificationChannelSingleEntityActionResult):
    """Result of validating a notification channel."""

    @override
    def target_entity_id(self) -> str:
        return ""
