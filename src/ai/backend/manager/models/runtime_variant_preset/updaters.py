from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, override
from uuid import UUID

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.runtime_variant_preset import RuntimeVariantPresetID
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    PresetTarget,
    PresetValueType,
    UIOption,
)
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.updater import DataUpdater
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class RuntimeVariantPresetUpdater(DataUpdater[RuntimeVariantPresetRow, RuntimeVariantPresetData]):
    preset_id: RuntimeVariantPresetID
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: TriState[str] = field(default_factory=TriState[str].nop)
    rank: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    preset_target: OptionalState[PresetTarget] = field(
        default_factory=OptionalState[PresetTarget].nop
    )
    value_type: OptionalState[PresetValueType] = field(
        default_factory=OptionalState[PresetValueType].nop
    )
    default_value: TriState[str] = field(default_factory=TriState[str].nop)
    key: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    required: OptionalState[bool] = field(default_factory=OptionalState[bool].nop)
    category: TriState[str] = field(default_factory=TriState[str].nop)
    display_name: TriState[str] = field(default_factory=TriState[str].nop)
    ui_option: TriState[UIOption] = field(default_factory=TriState[UIOption].nop)

    @property
    @override
    def row_class(self) -> type[RuntimeVariantPresetRow]:
        return RuntimeVariantPresetRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return RuntimeVariantPresetRow.id

    @override
    def target_id_value(self) -> UUID:
        return self.preset_id

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_values(self) -> dict[str, Any]:
        to_update: dict[str, Any] = {}
        self.name.update_dict(to_update, "name")
        self.description.update_dict(to_update, "description")
        self.rank.update_dict(to_update, "rank")
        self.preset_target.update_dict(to_update, "preset_target")
        self.value_type.update_dict(to_update, "value_type")
        self.default_value.update_dict(to_update, "default_value")
        self.key.update_dict(to_update, "key")
        self.required.update_dict(to_update, "required")
        self.category.update_dict(to_update, "category")
        self.display_name.update_dict(to_update, "display_name")
        self.ui_option.update_dict(to_update, "ui_option")
        return to_update

    @override
    def to_data(self, row: RuntimeVariantPresetRow) -> RuntimeVariantPresetData:
        return row.to_data()
