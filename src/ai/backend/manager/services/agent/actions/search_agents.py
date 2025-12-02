from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.agent.types import AgentData
from ai.backend.manager.repositories.base import Querier

from .base import AgentAction


@dataclass
class SearchAgentsAction(AgentAction):
    """Action to search agents."""

    querier: Optional[Querier] = None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "search_agents"

    @override
    def entity_id(self) -> Optional[str]:
        return None


@dataclass
class SearchAgentsActionResult(BaseActionResult):
    """Result of searching agents."""

    agents: list[AgentData]
    total_count: int

    @override
    def entity_id(self) -> Optional[str]:
        return None
