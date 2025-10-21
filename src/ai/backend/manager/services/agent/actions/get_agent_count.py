from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.agent.types import AgentFetchConditions
from ai.backend.manager.services.agent.actions.base import AgentAction


@dataclass
class GetAgentCountAction(AgentAction):
    conditions: AgentFetchConditions

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "get_agents"


@dataclass
class GetAgentCountActionResult(BaseActionResult):
    count: int

    @override
    def entity_id(self) -> Optional[str]:
        return None
