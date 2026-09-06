from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.runtime_variant_preset import (
    RUNTIME_VARIANT_PRESET_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.manager.actions.v2.ops.base import CreateGlobalOpsAction
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.runtime_variant_preset.creators import RuntimeVariantPresetCreator
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow


@dataclass
class CreateRuntimeVariantPresetAction(
    CreateGlobalOpsAction[RuntimeVariantPresetRow, RuntimeVariantPresetData]
):
    """Add a preset, taking the next rank within its variant."""

    creator: RuntimeVariantPresetCreator

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RUNTIME_VARIANT_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_runtime_variant_preset"

    @override
    def to_creator(self) -> RuntimeVariantPresetCreator:
        return self.creator
