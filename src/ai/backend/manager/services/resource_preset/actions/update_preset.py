import uuid
from dataclasses import dataclass
from typing import override

from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.repositories.base.updater import Updater
from ai.backend.manager.services.resource_preset.actions.base import ResourcePresetAction


@dataclass
class UpdateResourcePresetAction(ResourcePresetAction):
    updater: Updater[ResourcePresetRow]
    id: uuid.UUID | None
    name: str | None

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_update_resource_preset"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateResourcePresetActionResult:
    resource_preset: ResourcePresetData
