from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.resource import RuntimeVariantPresetConflict
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.runtime_variant_preset.types import UIOption
from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.repositories.base.types import IntegrityErrorCheck


@dataclass
class RuntimeVariantPresetCreatorSpec(CreatorSpec[RuntimeVariantPresetRow]):
    runtime_variant_id: UUID
    name: str
    description: str | None
    rank: int
    preset_target: str
    value_type: str
    default_value: str | None
    key: str
    category: str | None
    ui_type: str | None
    display_name: str | None
    ui_option: UIOption | None

    @property
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
        row.rank = self.rank
        row.preset_target = self.preset_target
        row.value_type = self.value_type
        row.default_value = self.default_value
        row.key = self.key
        row.category = self.category
        row.ui_type = self.ui_type
        row.display_name = self.display_name
        row.ui_option = self.ui_option
        return row
