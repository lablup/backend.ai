from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

import sqlalchemy as sa

from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.entity.runtime_variant_preset import RuntimeVariantPresetID
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    PresetTarget,
    PresetValueType,
    UIOption,
)
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.resource import RuntimeVariantPresetConflict
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.specs.creator import GlobalEntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck

__all__ = (
    "RANK_GAP",
    "RuntimeVariantPresetCreator",
)

RANK_GAP = 100


@dataclass
class RuntimeVariantPresetCreator(
    GlobalEntityCreator[RuntimeVariantPresetRow, RuntimeVariantPresetData]
):
    """Insert a preset, ranked last within its runtime variant.

    The rank is a subquery in the INSERT rather than a locked read before it, so two
    concurrent inserts can land on the same rank; rank only orders a catalog.
    """

    runtime_variant_id: RuntimeVariantID
    name: str
    description: str | None
    preset_target: PresetTarget
    value_type: PresetValueType
    default_value: str | None
    key: str
    required: bool
    category: str | None
    display_name: str | None
    ui_option: UIOption | None

    @override
    def entity_id(self, row: RuntimeVariantPresetRow) -> RuntimeVariantPresetID:
        return RuntimeVariantPresetID(row.id)

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=RuntimeVariantPresetConflict(
                    f"Duplicate runtime variant preset name: {self.name}"
                ),
            ),
        )

    @override
    def build_row(self) -> RuntimeVariantPresetRow:
        row = RuntimeVariantPresetRow()
        row.runtime_variant = self.runtime_variant_id
        row.name = self.name
        row.description = self.description
        row.rank = self._next_rank()
        row.preset_target = self.preset_target
        row.value_type = self.value_type
        row.default_value = self.default_value
        row.key = self.key
        row.required = self.required
        row.category = self.category
        row.display_name = self.display_name
        row.ui_option = self.ui_option
        return row

    @override
    def to_data(self, row: RuntimeVariantPresetRow) -> RuntimeVariantPresetData:
        return row.to_data()

    def _next_rank(self) -> sa.sql.elements.ColumnElement[int]:
        return (
            sa.select(sa.func.coalesce(sa.func.max(RuntimeVariantPresetRow.rank), 0) + RANK_GAP)
            .where(RuntimeVariantPresetRow.runtime_variant == self.runtime_variant_id)
            .scalar_subquery()
        )
