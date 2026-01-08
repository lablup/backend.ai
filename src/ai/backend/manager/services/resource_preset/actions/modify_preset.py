import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.resource_preset.actions.base import ResourcePresetAction


@dataclass
class ModifyResourcePresetAction(ResourcePresetAction):
    updater: Updater[ResourcePresetRow]
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
    resource_preset: ResourcePresetData

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.resource_preset.id)
