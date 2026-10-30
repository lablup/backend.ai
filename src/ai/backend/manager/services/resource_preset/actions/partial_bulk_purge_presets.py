from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.resource_preset import ResourcePresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeEntityOpsAction
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.models.resource_preset.purgers import ResourcePresetPurger
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow


@dataclass(frozen=True)
class PartialBulkPurgeResourcePresetsAction(
    PartialBulkPurgeEntityOpsAction[ResourcePresetRow, ResourcePresetData]
):
    """Remove the named resource presets for good, answering for each one."""

    ids: Sequence[ResourcePresetID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_purge_resource_presets"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_purgers(self) -> Mapping[EntityIdentifier, ResourcePresetPurger]:
        return {preset_id: ResourcePresetPurger(preset_id=preset_id) for preset_id in self.ids}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[preset_id for preset_id in self.ids if preset_id in allowed])
