from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, override

from ai.backend.manager.models.runtime_variant_preset.row import RuntimeVariantPresetRow
from ai.backend.manager.models.runtime_variant_preset.types import UIOption
from ai.backend.manager.repositories.base.updater import UpdaterSpec
from ai.backend.manager.types import OptionalState, TriState


@dataclass
class RuntimeVariantPresetUpdaterSpec(UpdaterSpec[RuntimeVariantPresetRow]):
    name: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    description: TriState[str] = field(default_factory=TriState[str].nop)
    rank: OptionalState[int] = field(default_factory=OptionalState[int].nop)
    preset_target: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    value_type: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    default_value: TriState[str] = field(default_factory=TriState[str].nop)
    key: OptionalState[str] = field(default_factory=OptionalState[str].nop)
    category: TriState[str] = field(default_factory=TriState[str].nop)
    ui_type: TriState[str] = field(default_factory=TriState[str].nop)
    display_name: TriState[str] = field(default_factory=TriState[str].nop)
    ui_option: TriState[UIOption] = field(default_factory=TriState[UIOption].nop)

    @property
    @override
    def row_class(self) -> type[RuntimeVariantPresetRow]:
        return RuntimeVariantPresetRow

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
        self.category.update_dict(to_update, "category")
        self.ui_type.update_dict(to_update, "ui_type")
        self.display_name.update_dict(to_update, "display_name")
        self.ui_option.update_dict(to_update, "ui_option")
        return to_update
