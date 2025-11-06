from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.notification import (
    NotificationChannelData,
    NotificationChannelModifier,
)

from .base import NotificationAction


@dataclass
class UpdateChannelAction(NotificationAction):
    """Action to update a notification channel."""

    channel_id: UUID
    modifier: NotificationChannelModifier

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.channel_id)


@dataclass
class UpdateChannelActionResult(BaseActionResult):
    """Result of updating a notification channel."""

    channel_data: NotificationChannelData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.channel_data.id)
