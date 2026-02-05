from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.session.types import SessionSchedulingHistoryData
from ai.backend.manager.repositories.base import BatchQuerier

from .base import SchedulingHistoryAction


@dataclass
class SearchSessionHistoryAction(SchedulingHistoryAction):
    """Action to search session scheduling history (admin API)."""

    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "session:history"

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search"

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class SearchSessionHistoryActionResult(BaseActionResult):
    """Result of searching session scheduling history."""

    histories: list[SessionSchedulingHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
