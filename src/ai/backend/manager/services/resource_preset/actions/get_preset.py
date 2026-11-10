from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_preset import ResourcePresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import GetSingleEntityOpsAction
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.models.resource_preset.queriers import ResourcePresetQuerier
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow


@dataclass
class GetResourcePresetAction(GetSingleEntityOpsAction[ResourcePresetRow, ResourcePresetData]):
    """Read the preset an id names.

    Single-entity rather than global: the read starts from the preset's id, the same
    end the update and the delete beside it start from. The catalog reads that answer
    a session launcher start from a resource group name instead and stay global and
    public -- ``global_list_resource_presets`` and ``global_check_resource_presets``.
    """

    preset_id: ResourcePresetID

    @override
    @classmethod
    def action_name(cls) -> str:
        return "get_resource_preset"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.preset_id

    @override
    def to_querier(self) -> ResourcePresetQuerier:
        return ResourcePresetQuerier(preset_id=self.preset_id)
