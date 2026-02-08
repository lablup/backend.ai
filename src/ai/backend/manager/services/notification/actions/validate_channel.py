from __future__ import annotations

from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType

from .base import NotificationAction


@dataclass
class ValidateChannelAction(NotificationAction):
    """Action to validate a notification channel (webhook sending test)."""

    channel_id: UUID
    test_message: str

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE

    @override
    def entity_id(self) -> str | None:
        return str(self.channel_id)


@dataclass
class ValidateChannelActionResult(BaseActionResult):
    """Result of validating a notification channel."""

    @override
    def entity_id(self) -> str | None:
        return None
