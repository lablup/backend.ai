from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.resource_preset import ResourcePresetEntityType
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import GlobalSearcherOpsAction
from ai.backend.manager.data.resource_preset.types import ResourcePresetData
from ai.backend.manager.models.resource_preset.row import ResourcePresetRow


@dataclass(frozen=True)
class SearchResourcePresetsV2Action(GlobalSearcherOpsAction[ResourcePresetRow, ResourcePresetData]):
    """Page through the resource preset catalog."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ResourcePresetEntityType()

    @override
    @classmethod
    def action_name(cls) -> str:
        return "global_search_resource_presets"
