from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.session.types import SessionSchedulingHistoryData
from ai.backend.manager.repositories.base import BatchQuerier
from ai.backend.manager.repositories.scheduling_history.types import (
    SessionSchedulingHistorySearchScope,
)

from .base import SchedulingHistoryAction


@dataclass
class SearchSessionScopedHistoryAction(SchedulingHistoryAction):
    """Action to search session scheduling history within a session scope.

    This is the scoped version used by entity-scoped APIs.
    Scope is required and specifies which session to query history for.
    """

    scope: SessionSchedulingHistorySearchScope
    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> str:
        return "session:scoped-history"

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search"

    @override
    def entity_id(self) -> str | None:
        return str(self.scope.session_id)


@dataclass
class SearchSessionScopedHistoryActionResult(BaseActionResult):
    """Result of searching session scheduling history within scope."""

    histories: list[SessionSchedulingHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
