from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    PresetTarget,
    PresetValueType,
)


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
class RuntimeVariantPresetData:
    id: UUID
    runtime_variant_id: UUID
    name: str
    description: str | None
    rank: int
    preset_target: PresetTarget
    value_type: PresetValueType
    default_value: str | None
    key: str
    category: str | None
    ui_type: str | None
    display_name: str | None
    ui_option: UIOptionData | None
    created_at: datetime
    updated_at: datetime | None
