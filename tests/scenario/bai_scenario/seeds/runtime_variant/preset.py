"""Write specs for a runtime variant preset."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from bai_scenario.seeds.seeder import Naming, SeedRowFrom

from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    PresetTarget,
    PresetValueType,
    UIOption,
)
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.runtime_variant_preset.creators import RuntimeVariantPresetCreator


@dataclass(frozen=True)
class SeedRuntimeVariantPreset(SeedRowFrom[RuntimeVariantData, RuntimeVariantPresetData]):
    """A preset of the variant laid before it. The insert ranks it last in that variant."""

    name_hint: str = "preset"
    description: str | None = "미리 만들어 둔 preset"
    preset_target: PresetTarget = PresetTarget.ENV
    value_type: PresetValueType = PresetValueType.STR
    default_value: str | None = None
    key: str = "PRESET_KEY"
    required: bool = False
    added_version: str | None = None
    deprecated_version: str | None = None
    category: str | None = None
    display_name: str | None = None
    ui_option: UIOption | None = None

    @override
    def kind(self) -> str:
        return "런타임 변형 preset"

    @override
    def detail(self) -> str:
        parts = [f"{self.preset_target.value} 대상, 값 종류 {self.value_type.value}"]
        if self.default_value is not None:
            parts.append(f"기본값 {self.default_value}")
        if self.added_version is not None or self.deprecated_version is not None:
            parts.append(
                f"버전 {self.added_version or '처음'}부터 {self.deprecated_version or '끝'}까지"
            )
        return ", ".join(parts)

    @override
    def name(self, naming: Naming) -> str:
        return naming(self.name_hint)

    @override
    def seed(self, name: str, source: RuntimeVariantData) -> RuntimeVariantPresetCreator:
        return RuntimeVariantPresetCreator(
            runtime_variant_id=RuntimeVariantID(source.id),
            name=name,
            description=self.description,
            preset_target=self.preset_target,
            value_type=self.value_type,
            default_value=self.default_value,
            key=self.key,
            required=self.required,
            added_version=self.added_version,
            deprecated_version=self.deprecated_version,
            category=self.category,
            display_name=self.display_name,
            ui_option=self.ui_option,
        )
