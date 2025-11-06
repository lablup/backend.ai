from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.notification import NotificationChannelData
from ai.backend.manager.repositories.base import Querier

from .base import NotificationAction


@dataclass
class ListChannelsAction(NotificationAction):
    """Action to list notification channels."""

    querier: Optional[Querier] = None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "list_channels"

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
