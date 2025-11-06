from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.notification import NotificationChannelData

from .base import NotificationAction


@dataclass
class ListChannelsAction(NotificationAction):
    """Action to list notification channels."""

    enabled_only: bool = False

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class ListChannelsActionResult(BaseActionResult):
    """Result of listing notification channels."""

    channels: list[NotificationChannelData]

    @override
    def entity_id(self) -> Optional[str]:
        return None
