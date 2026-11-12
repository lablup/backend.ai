"""Write specs for a runtime variant preset."""

from __future__ import annotations

from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    PresetTarget,
    PresetValueType,
    UIOption,
)
from ai.backend.manager.data.runtime_variant.types import RuntimeVariantData
from ai.backend.manager.data.runtime_variant_preset.types import RuntimeVariantPresetData
from ai.backend.manager.models.runtime_variant_preset.creators import RuntimeVariantPresetCreator
from ai.backend.testutils.scenario_steps import Language, Says, in_language
from bai_scenario.seeds.seeder import Naming, TestSeedRowFrom, joined


@dataclass(frozen=True)
class TestSeedRuntimeVariantPreset(TestSeedRowFrom[RuntimeVariantData, RuntimeVariantPresetData]):
    """A preset of the variant laid before it. The insert ranks it last in that variant."""

    name_hint: str = "preset"
    description: str | None = Says("미리 저장한 프리셋", english="a preset seeded in advance")
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
        return Says("런타임 파라미터", english="Runtime variant preset")

    @override
    def detail(self) -> str:
        parts: list[str] = [
            Says(
                f"대상 {self.preset_target.value}, 값 종류 {self.value_type.value}",
                english=f"target {self.preset_target.value}, value type {self.value_type.value}",
            )
        ]
        if self.default_value is not None:
            parts.append(
                Says(
                    f"기본값 {self.default_value}",
                    english=f"default value {self.default_value}",
                )
            )
        if self.added_version is not None or self.deprecated_version is not None:
            start = self.added_version or Says("처음", english="the first")
            end = self.deprecated_version or Says("끝", english="the last")
            parts.append(
                Says(
                    f"버전 {start}부터 {end}까지",
                    english=(
                        f"version from {in_language(start, Language.ENGLISH)} "
                        f"to {in_language(end, Language.ENGLISH)}"
                    ),
                )
            )
        return joined(parts)

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
