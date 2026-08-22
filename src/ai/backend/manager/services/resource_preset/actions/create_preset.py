from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.repositories.base.creator import Creator
from ai.backend.manager.services.resource_preset.actions.base import ResourcePresetAction


@dataclass
class CreateResourcePresetAction(ResourcePresetAction):
    creator: Creator[ResourcePresetRow]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_create_resource_preset"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.CREATE


@dataclass
class CreateResourcePresetActionResult:
    resource_preset: ResourcePresetData


# TODO: Create exceptions.
