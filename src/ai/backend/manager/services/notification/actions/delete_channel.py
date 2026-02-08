from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import NotificationAction


@dataclass
class DeleteChannelAction(NotificationAction):
    """Action to delete a notification channel."""

    channel_id: UUID

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE

    @override
    def entity_id(self) -> str | None:
        return str(self.channel_id)


@dataclass
class DeleteChannelActionResult(BaseActionResult):
    """Result of deleting a notification channel."""

    deleted: bool

    @override
    def entity_id(self) -> str | None:
        return None
