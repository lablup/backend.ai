from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_preset import ResourcePresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.types import ActionOperationType
from ai.backend.manager.actions.v2.single_entity.base import BaseSingleEntityAction
from ai.backend.manager.data.resource_preset.types import ResourcePresetData


@dataclass
class DeleteResourcePresetAction(BaseSingleEntityAction):
    """Remove one resource preset."""

    preset_id: ResourcePresetID

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.preset_id

    @override
    @classmethod
    def action_name(cls) -> str:
        return "delete_resource_preset"

    @override
    @classmethod
    def operation_type(cls) -> ActionOperationType:
        return ActionOperationType.DELETE


@dataclass
class DeleteResourcePresetActionResult:
    resource_preset: ResourcePresetData
