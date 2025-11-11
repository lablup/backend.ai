from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.notification import NotificationChannelData
from ai.backend.manager.repositories.base import Querier

from .base import NotificationAction


@dataclass
class SearchChannelsAction(NotificationAction):
    """Action to search notification channels."""

    querier: Optional[Querier] = None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search_channels"

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class SearchChannelsActionResult(BaseActionResult):
    """Result of searching notification channels."""

    channels: list[NotificationChannelData]
    total_count: int

    @override
    def entity_id(self) -> Optional[str]:
        return None
