from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.agent.types import AgentData
from ai.backend.manager.models.rbac.permission_defs import AgentPermission
from ai.backend.manager.repositories.base import Querier

from .base import AgentAction


@dataclass
class SearchAgentsAction(AgentAction):
    """Action to search agents."""

    querier: Querier

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
    permissions: list[AgentPermission]
    total_count: int
    has_next_page: bool
    has_previous_page: bool

    @override
    def entity_id(self) -> Optional[str]:
        return None
