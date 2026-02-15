from dataclasses import dataclass
from typing import override

from ai.backend.common.types import AgentId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.agent.types import AgentDetailData
from ai.backend.manager.services.agent.actions.base import AgentAction


@dataclass
class GetAgentAction(AgentAction):
    agent_id: AgentId

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET

    @override
    def entity_id(self) -> str | None:
        return str(self.agent_id)


@dataclass
class GetAgentActionResult(BaseActionResult):
    data: AgentDetailData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.agent.id)
