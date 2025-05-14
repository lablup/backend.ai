import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.services.resource_preset.actions.base import ResourcePresetAction
from ai.backend.manager.services.resource_preset.types import ResourcePresetModifier


@dataclass
class ModifyResourcePresetAction(ResourcePresetAction):
    modifier: ResourcePresetModifier
    id: Optional[uuid.UUID]
    name: Optional[str]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.id) if self.id else None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "modify"


@dataclass
class ModifyResourcePresetActionResult(BaseActionResult):
    # TODO: Create ResourcePresetRow type
    resource_preset: ResourcePresetRow

    @override
    def entity_id(self) -> Optional[str]:
        return self.resource_preset.id


# TODO: Create exceptions.
