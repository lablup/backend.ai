from dataclasses import dataclass
from typing import override

from ai.backend.common.data.image.types import ScannedImage
from ai.backend.common.types import AgentId, ImageCanonical
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.agent.actions.base import AgentAction


@dataclass
class RemoveAgentFromImagesAction(AgentAction):
    agent_id: AgentId
    scanned_images: dict[ImageCanonical, ScannedImage]

    @override
    def entity_id(self) -> str | None:
        return str(self.agent_id)

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class RemoveAgentFromImagesActionResult(BaseActionResult):
    agent_id: AgentId

    @override
    def entity_id(self) -> str | None:
        return str(self.agent_id)
