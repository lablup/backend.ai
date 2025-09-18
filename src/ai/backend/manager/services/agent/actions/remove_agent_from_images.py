from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import AgentId
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.agent.actions.base import AgentAction


@dataclass
class RemoveAgentFromImagesAction(AgentAction):
    agent_id: AgentId
    image_canonicals: list[str]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.agent_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "remove_agent_from_image"


@dataclass
class RemoveAgentFromImagesActionResult(BaseActionResult):
    agent_id: AgentId

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.agent_id)
