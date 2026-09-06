from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SESSION_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionSchedulingHistoryData
from ai.backend.manager.models.scheduling_history.scopes import (
    SessionSchedulingHistoryOperationScope,
)
from ai.backend.manager.repositories.base import BatchQuerier

from .base import SchedulingHistoryScopeActionResult, SessionSchedulingHistoryAction


@dataclass
class SearchSessionScopedHistoryAction(SessionSchedulingHistoryAction):
    """Action to search session scheduling history within a session scope.

    This is the scoped version used by entity-scoped APIs.
    Scope is required and specifies which session to query history for.
    """

    scope: SessionSchedulingHistoryOperationScope
    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SESSION_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_session_scoped_history"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchSessionScopedHistoryActionResult(SchedulingHistoryScopeActionResult):
    """Result of searching session scheduling history within scope."""

    histories: list[SessionSchedulingHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
