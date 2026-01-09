from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import AgentId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.agent import AgentStatus
from ai.backend.manager.services.agent.actions.base import AgentAction


@dataclass
class MarkAgentExitAction(AgentAction):
    agent_id: AgentId
    agent_status: AgentStatus

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.agent_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "mark_agent_exit"


@dataclass
class MarkAgentExitActionResult(BaseActionResult):
    agent_id: AgentId

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.agent_id)
