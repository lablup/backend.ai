from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.deployment_preset import (
    DEPLOYMENT_PRESET_ENTITY_TYPE,
    DeploymentPresetID,
)
from ai.backend.common.data.entity.types import EntityType, ScopeRef, ScopeType
from ai.backend.manager.actions.v2.ops.base import OperationScopeOpsAction
from ai.backend.manager.data.deployment_preset.types import PresetResourceSlotData
from ai.backend.manager.models.deployment_revision_preset.scopes import (
    DeploymentPresetSlotOperationScope,
)
from ai.backend.manager.models.deployment_revision_preset.searchers import (
    PresetResourceSlotSearcher,
)
from ai.backend.manager.models.resource_slot.row import PresetResourceSlotRow
from ai.backend.manager.models.scopes import OperationScope


@dataclass
class SearchPresetResourceSlotsAction(
    OperationScopeOpsAction[PresetResourceSlotRow, PresetResourceSlotData]
):
    """Page through the slot amounts inside one preset.

    The preset is the scope, so ops applies that condition. There is no unpaginated
    variant -- a caller that wants every slot passes no pagination.
    """

    preset_id: DeploymentPresetID
    searcher: PresetResourceSlotSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return DEPLOYMENT_PRESET_ENTITY_TYPE

    @override
    def scope_targets(self) -> Sequence[ScopeRef]:
        return (
            ScopeRef(scope_type=ScopeType(DEPLOYMENT_PRESET_ENTITY_TYPE), scope_id=self.preset_id),
        )

    @override
    @classmethod
    def available_scope_types(cls) -> Sequence[EntityType]:
        return (DEPLOYMENT_PRESET_ENTITY_TYPE,)

    @override
    def operation_scopes(self) -> Sequence[OperationScope]:
        return (DeploymentPresetSlotOperationScope(preset_id=self.preset_id),)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_deployment_preset_resource_slots"

    @override
    def to_searcher(self) -> PresetResourceSlotSearcher:
        return self.searcher
