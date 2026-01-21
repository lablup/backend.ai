from dataclasses import dataclass
from typing import Optional, override

from ai.backend.common.types import AgentId, ImageCanonical
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.agent.actions.base import AgentAction


@dataclass
class RemoveAgentFromImagesByCanonicalsAction(AgentAction):
    agent_id: AgentId
    image_canonicals: list[ImageCanonical]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.agent_id)

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "remove_agent_from_image_by_canonicals"


@dataclass
class RemoveAgentFromImagesByCanonicalsActionResult(BaseActionResult):
    agent_id: AgentId

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.agent_id)
