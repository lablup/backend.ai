from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.session import SESSION_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.session.types import SessionSchedulingHistoryData
from ai.backend.manager.repositories.base import BatchQuerier

from .base import SchedulingHistoryAction


@dataclass
class SearchSessionHistoryAction(SchedulingHistoryAction):
    """Action to search session scheduling history (admin API)."""

    querier: BatchQuerier

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return SESSION_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_session_history"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH


@dataclass
class SearchSessionHistoryActionResult:
    """Result of searching session scheduling history."""

    histories: list[SessionSchedulingHistoryData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
