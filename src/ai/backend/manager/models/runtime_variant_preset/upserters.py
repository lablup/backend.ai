from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.entity.runtime_variant_preset import RuntimeVariantPresetID
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    PresetTarget,
    PresetValueType,
    UIOption,
)
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.runtime_variant_preset.searchable_fields import (
    RuntimeVariantPresetSearchableFields,
)
from ai.backend.manager.models.specs.created_in import CreatedInPublic
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter

__all__ = ("RuntimeVariantPresetUpserter",)


@dataclass
class RuntimeVariantPresetUpserter(
    CreatedInPublic[RuntimeVariantPresetRow],
    EntityUpserter[RuntimeVariantPresetRow, RuntimeVariantPresetData],
):
    """Write a runtime variant preset under its stated id and rank. Conflict key: id."""

    id: RuntimeVariantPresetID
    runtime_variant_id: RuntimeVariantID
    name: str
    description: str | None
    rank: int
    preset_target: PresetTarget
    value_type: PresetValueType
    default_value: str | None
    key: str
    required: bool
    added_version: str | None
    deprecated_version: str | None
    category: str | None
    display_name: str | None
    ui_option: UIOption | None

    @override
    def entity_id(self, row: RuntimeVariantPresetRow) -> RuntimeVariantPresetID:
        return RuntimeVariantPresetID(row.id)

    @override
    def row_class(self) -> type[RuntimeVariantPresetRow]:
        return RuntimeVariantPresetRow

    @override
    def index_elements(self) -> list[str]:
        return ["id"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {"id": self.id, **self._values()}

    @override
    def build_update_values(self) -> dict[str, Any]:
        """``updated_at`` is set here: ``ON CONFLICT DO UPDATE`` bypasses the ORM's
        ``onupdate``."""
        return {**self._values(), "updated_at": sa.func.now()}

    def _values(self) -> dict[str, Any]:
        return {
            "runtime_variant": self.runtime_variant_id,
            "name": self.name,
            "description": self.description,
            "rank": self.rank,
            "preset_target": self.preset_target,
            "value_type": self.value_type,
            "default_value": self.default_value,
            "key": self.key,
            "required": self.required,
            "added_version": self.added_version,
            "deprecated_version": self.deprecated_version,
            "category": self.category,
            "display_name": self.display_name,
            "ui_option": self.ui_option,
        }

    @override
    def to_data(self, row: RuntimeVariantPresetRow) -> RuntimeVariantPresetData:
        return RuntimeVariantPresetSearchableFields.own.to_data(row)
