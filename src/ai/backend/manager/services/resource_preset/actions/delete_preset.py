import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.services.resource_preset.actions.base import ResourcePresetAction


@dataclass
class DeleteResourcePresetAction(ResourcePresetAction):
    id: uuid.UUID | None
    name: str | None

    @override
    def entity_id(self) -> str | None:
        return str(self.id) if self.id else None

    @override
    @classmethod
    def operation_type(cls) -> str:
        return "delete"


@dataclass
class DeleteResourcePresetActionResult(BaseActionResult):
    resource_preset: ResourcePresetData

    @override
    def entity_id(self) -> str | None:
        return str(self.resource_preset.id)


# TODO: Create exceptions.
