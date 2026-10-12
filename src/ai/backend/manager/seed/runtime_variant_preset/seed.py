from __future__ import annotations

from collections.abc import Sequence
from typing import Self, override

from pydantic import Field, model_validator

from ai.backend.common.data.entity.runtime_variant import RuntimeVariantID
from ai.backend.common.data.entity.runtime_variant_preset import RuntimeVariantPresetID
from ai.backend.common.dto.manager.v2.common import SemVersion
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    VALUE_TYPE_VALIDATORS,
    PresetTarget,
    PresetValueType,
    UIOption,
)
from ai.backend.manager.models.runtime_variant_preset.upserters import (
    RuntimeVariantPresetUpserter,
)
from ai.backend.manager.repositories.ops.v2.seed.types import SeedWrite
from ai.backend.manager.seed.base import SeedItem, SeedItems, SeedRejection


class RuntimeVariantPresetSeed(SeedItem):
    """One ``runtime_variant_presets`` row under its stated id and rank."""

    id: RuntimeVariantPresetID
    runtime_variant_id: RuntimeVariantID
    name: str = Field(min_length=1, max_length=256)
    description: str | None = None
    rank: int = Field(ge=0)
    preset_target: PresetTarget
    value_type: PresetValueType
    default_value: str | None = Field(default=None, max_length=512)
    preset_key: str = Field(alias="key", min_length=1, max_length=256)
    required: bool = False
    added_version: SemVersion | None = None
    deprecated_version: SemVersion | None = None
    category: str | None = Field(default=None, max_length=64)
    display_name: str | None = Field(default=None, max_length=256)
    ui_option: UIOption | None = None

    @model_validator(mode="after")
    def _validate_flag_requires_args(self) -> Self:
        if self.value_type == PresetValueType.FLAG and self.preset_target != PresetTarget.ARGS:
            raise ValueError("value_type 'flag' is only valid with preset_target 'args'.")
        return self

    @model_validator(mode="after")
    def _validate_default_value(self) -> Self:
        if self.default_value is None:
            return self
        try:
            VALUE_TYPE_VALIDATORS[self.value_type](self.default_value)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"default_value '{self.default_value}' is not a valid {self.value_type}: {e}"
            ) from e
        return self

    @override
    def key(self) -> str:
        return str(self.id)

    @override
    def write(self) -> SeedWrite:
        return SeedWrite(
            upserter=RuntimeVariantPresetUpserter(
                id=self.id,
                runtime_variant_id=self.runtime_variant_id,
                name=self.name,
                description=self.description,
                rank=self.rank,
                preset_target=self.preset_target,
                value_type=self.value_type,
                default_value=self.default_value,
                key=self.preset_key,
                required=self.required,
                added_version=self.added_version,
                deprecated_version=self.deprecated_version,
                category=self.category,
                display_name=self.display_name,
                ui_option=self.ui_option,
            ),
            field_upserters=[],
            field_purgers=[],
        )

    @override
    @classmethod
    def reject(cls, files: Sequence[SeedItems[RuntimeVariantPresetSeed]]) -> list[SeedRejection]:
        return []
