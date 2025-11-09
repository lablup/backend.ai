from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.notification import NotificationChannelData

from .base import NotificationAction


@dataclass
class GetChannelAction(NotificationAction):
    """Action to get a notification channel by ID."""

    channel_id: UUID

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_channel"

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.channel_id)


@dataclass
class GetChannelActionResult(BaseActionResult):
    """Result of getting a notification channel."""

    channel_data: NotificationChannelData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.channel_data.id)
