from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment_preset import DeploymentPresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import BulkScopedSearchOpsAction
from ai.backend.manager.data.deployment_preset.types import PresetResourceSlotData
from ai.backend.manager.models.deployment_revision_preset.scopes import (
    DeploymentPresetSlotTarget,
)
from ai.backend.manager.models.deployment_revision_preset.searchers import (
    PresetResourceSlotSearcher,
)
from ai.backend.manager.models.resource_slot.row import PresetResourceSlotRow
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class SearchPresetResourceSlotsAction(
    BulkScopedSearchOpsAction[PresetResourceSlotRow, PresetResourceSlotData]
):
    """Page through the slot amounts inside the presets named, combined with OR.

    Every preset is authorized before the read runs. There is no unpaginated variant --
    a caller that wants every slot passes no pagination.
    """

    preset_ids: Sequence[DeploymentPresetID]
    searcher: PresetResourceSlotSearcher

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_deployment_preset_resource_slots"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.preset_ids)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return [DeploymentPresetSlotTarget(preset_id=preset_id) for preset_id in self.preset_ids]

    @override
    def to_searcher(self) -> PresetResourceSlotSearcher:
        return self.searcher
