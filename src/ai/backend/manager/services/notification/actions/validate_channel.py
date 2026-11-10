from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.notification import NotificationChannelID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction


@dataclass
class ValidateChannelAction(BaseSingleEntityAction):
    """Send a test message through a channel to prove it is reachable."""

    channel_id: NotificationChannelID
    test_message: str

    @override
    @classmethod
    def action_name(cls) -> str:
        return "validate_notification_channel"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.channel_id


@dataclass
class ValidateChannelActionResult:
    """Result of validating a notification channel."""
