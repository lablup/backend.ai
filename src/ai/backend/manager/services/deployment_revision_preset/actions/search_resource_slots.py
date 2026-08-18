from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.field.ops import SearchFieldOpsAction
from ai.backend.manager.data.deployment_preset.types import PresetResourceSlotData
from ai.backend.manager.models.resource_slot.row import PresetResourceSlotRow
from ai.backend.manager.repositories.deployment_revision_preset.searchers import (
    PresetResourceSlotSearcher,
)


@dataclass
class SearchPresetResourceSlotsAction(
    SearchFieldOpsAction[PresetResourceSlotRow, PresetResourceSlotData]
):
    """Page through the slot amounts one preset declares.

    The preset is named, so this is answered for by a read of the preset itself.
    """

    preset_id: DeploymentPresetID
    searcher: PresetResourceSlotSearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_deployment_preset_resource_slots"

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.preset_id

    @override
    def to_searcher(self) -> PresetResourceSlotSearcher:
        return self.searcher
