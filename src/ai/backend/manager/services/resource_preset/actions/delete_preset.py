import uuid
from dataclasses import dataclass
from typing import Optional, override

from ai.backend.manager.actions.action import BaseActionResult
from ai.backend.manager.services.resource_preset.base import ResourcePresetAction


@dataclass
class DeleteResourcePresetAction(ResourcePresetAction):
    id: Optional[uuid.UUID] = None
    name: Optional[str] = None

    @override
    def entity_id(self) -> Optional[str]:
        return str(self.id) if self.id else None

    @override
    def operation_type(self):
        return "delete_resource_preset"


@dataclass
class DeleteResourcePresetActionResult(BaseActionResult):
    # TODO: ResourcePresetRow 필드 추가해야함.
    # resource_preset: ResourcePresetRow

    @override
    def entity_id(self) -> Optional[str]:
        # return self.resource_preset.id
        return None


# TODO: 예외 만들 것.
