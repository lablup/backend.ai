from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.runtime_variant_preset import (
    RUNTIME_VARIANT_PRESET_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import SearchGlobalOpsAction
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.repositories.runtime_variant_preset.searchers import (
    RuntimeVariantPresetSearcher,
)


@dataclass
class SearchRuntimeVariantPresetsAction(
    SearchGlobalOpsAction[RuntimeVariantPresetRow, RuntimeVariantPresetData]
):
    """Page through the preset catalog."""

    searcher: RuntimeVariantPresetSearcher

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RUNTIME_VARIANT_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "search_runtime_variant_presets"

    @override
    def to_searcher(self) -> RuntimeVariantPresetSearcher:
        return self.searcher
