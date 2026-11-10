from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Self, override

from ai.backend.common.data.entity.runtime_variant_preset import RuntimeVariantPresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.actions.v2.ops.base import PartialBulkPurgeEntityOpsAction
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.runtime_variant_preset.purgers import RuntimeVariantPresetPurger
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow


@dataclass(frozen=True)
class PartialBulkPurgeRuntimeVariantPresetsAction(
    PartialBulkPurgeEntityOpsAction[RuntimeVariantPresetRow, RuntimeVariantPresetData]
):
    """Remove the named presets from their variants' catalogs, answering for each one."""

    ids: Sequence[RuntimeVariantPresetID]

    @override
    @classmethod
    def action_name(cls) -> str:
        return "partial_bulk_purge_runtime_variant_presets"

    @override
    def entity_ids(self) -> Sequence[EntityIdentifier]:
        return tuple(self.ids)

    @override
    def to_purgers(self) -> Mapping[EntityIdentifier, RuntimeVariantPresetPurger]:
        return {
            preset_id: RuntimeVariantPresetPurger(preset_id=preset_id) for preset_id in self.ids
        }

    @override
    def narrowed_to(self, entity_ids: Sequence[EntityIdentifier]) -> Self:
        allowed = frozenset(entity_ids)
        return replace(self, ids=[preset_id for preset_id in self.ids if preset_id in allowed])
