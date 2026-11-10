from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import UpdatePartialBulkOpsAction
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow
from ai.backend.manager.models.resource_preset.updaters import ResourcePresetUpdater


@dataclass(frozen=True)
class PartialBulkUpdateResourcePresetsAction(
    UpdatePartialBulkOpsAction[ResourcePresetRow, ResourcePresetData]
):
    """Retune the named resource presets, answering for each one."""

    updaters: Sequence[ResourcePresetUpdater]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_update_resource_presets"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(updater.preset_id for updater in self.updaters)

    @override
    def to_updaters(self) -> Mapping[EntityIdentifier, ResourcePresetUpdater]:
        return {updater.preset_id: updater for updater in self.updaters}

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(
            self, updaters=[updater for updater in self.updaters if updater.preset_id in allowed]
        )
