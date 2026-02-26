from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.agent.types import AgentData
from ai.backend.manager.models.agent import AgentRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.agent.actions.base import AgentAction


@dataclass
class CreateAgentAction(AgentAction):
    creator: Creator[AgentRow]

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateAgentActionResult(BaseActionResult):
    data: AgentData

    @override
    def entity_id(self) -> str | None:
        return str(self.data.id)
