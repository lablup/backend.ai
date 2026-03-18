from dataclasses import dataclass
from typing import override

from ai.backend.common.data.agent.types import AgentInfo
from ai.backend.common.types import AgentId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.agent.actions.base import AgentAction


@dataclass
class HandleHeartbeatAction(AgentAction):
    agent_id: AgentId
    agent_info: AgentInfo

    @override
    def entity_id(self) -> str | None:
        return str(self.agent_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class HandleHeartbeatActionResult(BaseActionResult):
    agent_id: AgentId

    @override
    def entity_id(self) -> str | None:
        return str(self.agent_id)
