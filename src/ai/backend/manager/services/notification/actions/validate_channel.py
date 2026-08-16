from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.notification import (
    NOTIFICATION_CHANNEL_ENTITY_TYPE,
    NotificationChannelID,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.global_scope.base import BaseGlobalAction


@dataclass
class ValidateChannelAction(BaseGlobalAction):
    """Send a test message through a channel to prove it is reachable."""

    channel_id: NotificationChannelID
    test_message: str

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return NOTIFICATION_CHANNEL_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "validate_notification_channel"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class ValidateChannelActionResult(BaseActionResult):
    """Result of validating a notification channel."""

    @override
    def entity_id(self) -> str | None:
        return None
