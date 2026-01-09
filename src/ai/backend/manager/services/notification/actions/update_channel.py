from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.notification import NotificationChannelData
from ai.backend.manager.models.notification import NotificationChannelRow
from ai.backend.manager.repositories.base.updater import Updater

from .base import NotificationAction


@dataclass
class UpdateChannelAction(NotificationAction):
    """Action to update a notification channel."""

    updater: Updater[NotificationChannelRow]

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "update_channel"

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.updater.pk_value)


@dataclass
class UpdateChannelActionResult(BaseActionResult):
    """Result of updating a notification channel."""

    channel_data: NotificationChannelData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.channel_data.id)
