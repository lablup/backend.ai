from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.runtime_variant_preset import (
    RUNTIME_VARIANT_PRESET_ENTITY_TYPE,
)
from ai.backend.common.data.entity.types import EntityType
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.runtime_variant_preset import RuntimeVariantPresetID
from ai.backend.manager.actions.v2.ops.base import PurgeEntityOpsAction
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.runtime_variant_preset.purgers import RuntimeVariantPresetPurger
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow


@dataclass
class PurgeRuntimeVariantPresetAction(
    PurgeEntityOpsAction[RuntimeVariantPresetRow, RuntimeVariantPresetData]
):
    """Remove a preset from its variant's catalog.

    Purge-shaped: the table carries no lifecycle column, so removing one has always
    been the row leaving the table.
    """

    id: RuntimeVariantPresetID

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RUNTIME_VARIANT_PRESET_ENTITY_TYPE

    @override
    @classmethod
    def action_name(cls) -> str:
        return "purge_runtime_variant_preset"

    @override
    def entity_id(self) -> EntityID:
        return self.to_purger().entity_id()

    @override
    def to_purger(self) -> RuntimeVariantPresetPurger:
        return RuntimeVariantPresetPurger(preset_id=self.id)
