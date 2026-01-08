from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.notification import NotificationChannelData
from ai.backend.manager.repositories.base import BatchQuerier

from .base import NotificationAction


@dataclass
class SearchChannelsAction(NotificationAction):
    """Action to search notification channels."""

    querier: BatchQuerier

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
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
