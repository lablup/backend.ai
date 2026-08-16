from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.identifier.runtime_variant_preset import RuntimeVariantPresetID
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class RuntimeVariantPresetPurger(EntityPurger[RuntimeVariantPresetRow, RuntimeVariantPresetData]):
    """Purger for removing a preset from a runtime variant's catalog."""

    preset_id: RuntimeVariantPresetID

    @override
    def row_class(self) -> type[RuntimeVariantPresetRow]:
        return RuntimeVariantPresetRow

    @override
    def pk_value(self) -> RuntimeVariantPresetID:
        return self.preset_id

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.preset_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: RuntimeVariantPresetRow) -> RuntimeVariantPresetData:
        return row.to_data()
