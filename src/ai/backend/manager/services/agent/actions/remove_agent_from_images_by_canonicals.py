from dataclasses import dataclass
from typing import override

from ai.backend.common.types import AgentId, ImageCanonical
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.agent.actions.base import AgentAction


@dataclass
class RemoveAgentFromImagesByCanonicalsAction(AgentAction):
    agent_id: AgentId
    image_canonicals: list[ImageCanonical]

    @override
    def entity_id(self) -> str | None:
        return str(self.agent_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class RemoveAgentFromImagesByCanonicalsActionResult(BaseActionResult):
    agent_id: AgentId

    @override
    def entity_id(self) -> str | None:
        return str(self.agent_id)
