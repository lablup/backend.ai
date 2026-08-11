from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import override

from ai.backend.common.data.entity.types import EntityData
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    PresetTarget,
    PresetValueType,
)
from ai.backend.common.identifier.entity import EntityID
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID
from ai.backend.common.identifier.runtime_variant_preset import RuntimeVariantPresetID


@dataclass(frozen=True)
class RuntimeVariantPresetValueData:
    """A concrete value bound to a runtime variant preset (by 'preset_id')."""

    preset_id: RuntimeVariantPresetID
    value: str


@dataclass(frozen=True)
class SliderOptionData:
    min: float
    max: float
    step: float


@dataclass(frozen=True)
class NumberOptionData:
    min: float | None
    max: float | None


@dataclass(frozen=True)
class ChoiceItemData:
    value: str
    label: str


@dataclass(frozen=True)
class ChoiceOptionData:
    items: list[ChoiceItemData]


@dataclass(frozen=True)
class TextOptionData:
    placeholder: str | None


@dataclass(frozen=True)
class UIOptionData:
    ui_type: str
    slider: SliderOptionData | None
    number: NumberOptionData | None
    choices: ChoiceOptionData | None
    text: TextOptionData | None


@dataclass(frozen=True)
class RuntimeVariantPresetData(EntityData):
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
    category: str | None
    ui_type: str | None
    display_name: str | None
    ui_option: UIOptionData | None
    created_at: datetime
    updated_at: datetime | None

    @override
    def entity_id(self) -> EntityID:
        return self.id
