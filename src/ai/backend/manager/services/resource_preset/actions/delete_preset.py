import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.services.resource_preset.actions.base import ResourcePresetAction


@dataclass
class DeleteResourcePresetAction(ResourcePresetAction):
    id: uuid.UUID | None
    name: str | None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_delete_resource_preset"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteResourcePresetActionResult:
    resource_preset: ResourcePresetData


# TODO: Create exceptions.
