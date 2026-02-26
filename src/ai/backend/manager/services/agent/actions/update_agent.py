from dataclasses import dataclass
from typing import override

from ai.backend.common.types import AgentId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.agent.types import AgentData
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.agent.actions.base import AgentAction


@dataclass
class UpdateAgentAction(AgentAction):
    agent_id: AgentId
    updater: Updater[AgentRow]

    @override
    def entity_id(self) -> str | None:
        return str(self.agent_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateAgentActionResult(BaseActionResult):
    data: AgentData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id)
