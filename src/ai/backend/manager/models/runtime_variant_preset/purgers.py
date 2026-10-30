from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.entity.runtime_variant_preset import RuntimeVariantPresetID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.runtime_variant_preset.searchable_fields import (
    RuntimeVariantPresetSearchableFields,
)
from ai.backend.manager.models.specs.purger import EntityBatchPurger, EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class RuntimeVariantPresetPurger(EntityPurger[RuntimeVariantPresetRow, RuntimeVariantPresetData]):
    """Purger for removing a preset from a runtime variant's catalog."""

    preset_id: RuntimeVariantPresetID

    @override
    def row_class(self) -> type[RuntimeVariantPresetRow]:
        return RuntimeVariantPresetRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return RuntimeVariantPresetRow.id

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.preset_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: RuntimeVariantPresetRow) -> RuntimeVariantPresetData:
        return RuntimeVariantPresetSearchableFields.own.to_data(row)


@dataclass
class RuntimeVariantPresetsOfVariantPurger(
    EntityBatchPurger[RuntimeVariantPresetRow, RuntimeVariantPresetData]
):
    """Every preset in one runtime variant's catalog, cleared before the variant goes."""

    variant_id: RuntimeVariantID

    @override
    def entity_id(self, row: RuntimeVariantPresetRow) -> EntityIdentifier:
        return RuntimeVariantPresetID(row.id)

    @override
    def build_subquery(self) -> sa.sql.Select[tuple[RuntimeVariantPresetRow]]:
        return sa.select(RuntimeVariantPresetRow).where(
            RuntimeVariantPresetRow.runtime_variant == self.variant_id
        )

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: RuntimeVariantPresetRow) -> RuntimeVariantPresetData:
        return RuntimeVariantPresetSearchableFields.own.to_data(row)
