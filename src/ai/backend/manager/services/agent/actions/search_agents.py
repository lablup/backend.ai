from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.agent.types import AgentDetailData
from ai.backend.manager.repositories.base import BatchQuerier

from .base import AgentAction


@dataclass
class SearchAgentsAction(AgentAction):
    querier: BatchQuerier

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.SEARCH

    @override
    def entity_id(self) -> str | None:
        return None


@dataclass
class SearchAgentsActionResult(BaseActionResult):
    """Result of searching agents with their permissions."""

    agents: list[AgentDetailData]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> str | None:
        return None
