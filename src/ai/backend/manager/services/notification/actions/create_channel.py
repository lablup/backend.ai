from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.notification import (
    NotificationChannelCreator,
    NotificationChannelData,
)

from .base import NotificationAction


@dataclass
class CreateChannelAction(NotificationAction):
    """Action to create a notification channel."""

    creator: NotificationChannelCreator

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create_channel"

    @override
    def entity_id(self) -> Optional[str]:
        return self.creator.name


@dataclass
class CreateChannelActionResult(BaseActionResult):
    """Result of creating a notification channel."""

    channel_data: NotificationChannelData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.channel_data.id)
