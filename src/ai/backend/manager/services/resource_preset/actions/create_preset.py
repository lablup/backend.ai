from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.services.resource_preset.actions.base import ResourcePresetAction
from ai.backend.manager.services.resource_preset.types import ResourcePresetCreator


@dataclass
class CreateResourcePresetAction(ResourcePresetAction):
    creator: ResourcePresetCreator

    @override
    def entity_id(self) -> Optional[str]:
        return None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "create"


@dataclass
class CreateResourcePresetActionResult(BaseActionResult):
    # TODO: Use dataclass instead of Row
    resource_preset: ResourcePresetRow

    @override
    def entity_id(self) -> Optional[str]:
        return self.resource_preset.id


# TODO: Create exceptions.
