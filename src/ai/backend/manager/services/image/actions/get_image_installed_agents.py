from collections.abc import Mapping
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.permission.types import EntityType
from ai.backend.common.types import AgentId, ImageID
from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.services.image.actions.base import ImageAction


@dataclass
class GetImageInstalledAgentsAction(ImageAction):
    image_ids: list[ImageID]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return EntityType.IMAGE_AGENT

    @override
    def entity_id(self) -> str | None:
        return None

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.GET


@dataclass
class GetImageInstalledAgentsActionResult(BaseActionResult):
    data: Mapping[ImageID, set[AgentId]]

    @override
    def entity_id(self) -> str | None:
        return None
