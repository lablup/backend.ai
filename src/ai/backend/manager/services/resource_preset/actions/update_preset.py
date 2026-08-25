from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_preset import ResourcePresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.models.resource_preset import ResourcePresetRow
from ai.backend.manager.repositories.base.updater import Updater


@dataclass
class UpdateResourcePresetAction(BaseSingleEntityAction):
    """Retune one resource preset."""

    preset_id: ResourcePresetID
    updater: Updater[ResourcePresetRow]

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.preset_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "update_resource_preset"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.UPDATE


@dataclass
class UpdateResourcePresetActionResult:
    resource_preset: ResourcePresetData
