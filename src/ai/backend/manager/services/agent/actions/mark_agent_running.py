from dataclasses import dataclass
from typing import override

from ai.backend.common.types import AgentId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.models.agent import AgentStatus
from ai.backend.manager.services.agent.actions.base import AgentAction


@dataclass
class MarkAgentRunningAction(AgentAction):
    agent_id: AgentId
    agent_status: AgentStatus

    @override
    def entity_id(self) -> str | None:
        return str(self.agent_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class MarkAgentRunningActionResult(BaseActionResult):
    agent_id: AgentId

    @override
    def entity_id(self) -> str | None:
        return str(self.agent_id)
