from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override
from uuid import UUID

from ai.backend.manager.actions.action import BaseActionResult

from .base import NotificationAction


@dataclass
class ValidateChannelAction(NotificationAction):
    """Action to validate a notification channel (webhook sending test)."""

    channel_id: UUID
    test_message: str

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "validate_channel"

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.channel_id)


@dataclass
class ValidateChannelActionResult(BaseActionResult):
    """Result of validating a notification channel."""

    @override
    def entity_id(self) -> Optional[str]:
        return None
