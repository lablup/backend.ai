from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult

from .base import NotificationAction


@dataclass
class DeleteChannelAction(NotificationAction):
    """Action to delete a notification channel."""

    channel_id: UUID

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete_channel"

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.channel_id)


@dataclass
class DeleteChannelActionResult(BaseActionResult):
    """Result of deleting a notification channel."""

    deleted: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
