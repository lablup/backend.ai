import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.services.resource_preset.actions.base import ResourcePresetAction


@dataclass
class DeleteResourcePresetAction(ResourcePresetAction):
    id: Optional[uuid.UUID]
    name: Optional[str]

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.id) if self.id else None

    @override
    def operation_type(self):
        return "delete"


@dataclass
class DeleteResourcePresetActionResult(BaseActionResult):
    # TODO: Add ResourcePresetRow field.
    resource_preset: ResourcePresetRow

    @override
    def entity_id(self) -> Optional[str]:
        return self.resource_preset.id


# TODO: Create exceptions.
