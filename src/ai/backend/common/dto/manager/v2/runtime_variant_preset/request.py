from __future__ import annotations

from typing import Self
from uuid import UUID

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import BaseRequestModel
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection, SemVersion
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    VALUE_TYPE_VALIDATORS,
    PresetTarget,
    PresetValueType,
    RuntimeVariantPresetOrderField,
    UIOption,
)
from ai.backend.common.tristate.unset import UNSET, Unset


class CreateRuntimeVariantPresetInput(BaseRequestModel):
    runtime_variant_id: UUID = Field(
        description="ID of the runtime variant this preset belongs to."
    )
    name: str = Field(min_length=1, max_length=256, description="Preset name.")
    description: str | None = Field(default=None, description="Description.")
    preset_target: PresetTarget = Field(description="Target: env or args.")
    value_type: PresetValueType = Field(
        description=(
            "Value type: str, int, float, bool, flag. "
            "'flag' is only valid with preset_target 'args'."
        )
    )
    default_value: str | None = Field(default=None, max_length=512, description="Default value.")
    key: str = Field(min_length=1, max_length=256, description="Env key or args flag.")
    required: bool = Field(
        default=False,
        description="Whether this preset param must be supplied on a deployment revision.",
    )
    added_version: SemVersion | None = Field(
        default=None,
        description="Runtime version this preset became available in; None means always.",
    )
    deprecated_version: SemVersion | None = Field(
        default=None,
        description=(
            "Runtime version this preset was removed in, exclusive; None means not removed."
        ),
    )
    category: str | None = Field(default=None, max_length=64, description="UI category group.")
    display_name: str | None = Field(default=None, max_length=256, description="UI display name.")
    ui_option: UIOption | None = Field(
        default=None, description="UI rendering option. Contains ui_type and type-specific config."
    )

    @model_validator(mode="after")
    def validate_flag_requires_args(self) -> Self:
        if self.value_type == PresetValueType.FLAG and self.preset_target != PresetTarget.ARGS:
            raise ValueError("value_type 'flag' is only valid with preset_target 'args'.")
        return self

    @model_validator(mode="after")
    def validate_default_value(self) -> Self:
        if self.default_value is None:
            return self
        validator = VALUE_TYPE_VALIDATORS.get(self.value_type)
        if validator is None:
            return self
        try:
            validator(self.default_value)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"default_value '{self.default_value}' is not a valid {self.value_type}: {e}"
            ) from e
        return self


class UpdateRuntimeVariantPresetInput(BaseRequestModel):
    id: UUID = Field(description="Preset ID.")
    name: str | None | Unset = Field(
        default=UNSET, min_length=1, max_length=256, description="Omit to leave unchanged."
    )
    description: str | None | Unset = Field(
        default=UNSET, description="Description. Omit to leave unchanged; null clears."
    )
    rank: int | None | Unset = Field(default=UNSET, ge=0, description="Omit to leave unchanged.")
    preset_target: PresetTarget | None | Unset = Field(
        default=UNSET, description="Omit to leave unchanged."
    )
    value_type: PresetValueType | None | Unset = Field(
        default=UNSET,
        description=(
            "New value type. 'flag' is only valid when the effective preset_target is 'args' "
            "(the stored target applies when preset_target is omitted). Omit to leave unchanged."
        ),
    )
    default_value: str | None | Unset = Field(
        default=UNSET, description="Default value. Omit to leave unchanged; null clears."
    )
    key: str | None | Unset = Field(
        default=UNSET, min_length=1, max_length=256, description="Omit to leave unchanged."
    )
    required: bool | None | Unset = Field(
        default=UNSET, description="Toggle required flag. Omit to leave unchanged."
    )
    category: str | None | Unset = Field(
        default=UNSET, description="UI category group. Omit to leave unchanged; null clears."
    )
    display_name: str | None | Unset = Field(
        default=UNSET, description="UI display name. Omit to leave unchanged; null clears."
    )
    ui_option: UIOption | None | Unset = Field(
        default=UNSET,
        description="UI rendering option. Omit to leave unchanged; null clears.",
    )
    added_version: SemVersion | None | Unset = Field(default=UNSET)
    deprecated_version: SemVersion | None | Unset = Field(default=UNSET)

    @model_validator(mode="after")
    def validate_flag_requires_args(self) -> Self:
        if (
            self.value_type == PresetValueType.FLAG
            and isinstance(self.preset_target, PresetTarget)
            and self.preset_target != PresetTarget.ARGS
        ):
            raise ValueError("value_type 'flag' is only valid with preset_target 'args'.")
        return self

    @model_validator(mode="after")
    def validate_default_value(self) -> Self:
        if isinstance(self.value_type, Unset) or self.value_type is None:
            return self
        if isinstance(self.default_value, Unset) or self.default_value is None:
            return self
        validator = VALUE_TYPE_VALIDATORS.get(self.value_type)
        if validator is None:
            return self
        try:
            validator(self.default_value)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"default_value '{self.default_value}' is not a valid {self.value_type}: {e}"
            ) from e
        return self


class RuntimeVariantPresetFilter(BaseRequestModel):
    name: StringFilter | None = Field(default=None)
    runtime_variant_id: UUIDFilter | None = Field(default=None)
    runtime_version: SemVersion | None = Field(
        default=None,
        description=(
            "Keep only presets valid at this runtime version "
            "(added_version <= version < deprecated_version)."
        ),
    )
    AND: list[RuntimeVariantPresetFilter] | None = Field(default=None)
    OR: list[RuntimeVariantPresetFilter] | None = Field(default=None)
    NOT: list[RuntimeVariantPresetFilter] | None = Field(default=None)


RuntimeVariantPresetFilter.model_rebuild()


class RuntimeVariantPresetOrder(BaseRequestModel):
    field: RuntimeVariantPresetOrderField
    direction: OrderDirection = OrderDirection.ASC


class SearchRuntimeVariantPresetsInput(BaseRequestModel):
    filter: RuntimeVariantPresetFilter | None = Field(default=None)
    order: list[RuntimeVariantPresetOrder] | None = Field(default=None)
    first: int | None = Field(default=None, ge=1)
    after: str | None = Field(default=None)
    last: int | None = Field(default=None, ge=1)
    before: str | None = Field(default=None)
    limit: int | None = Field(default=None, ge=1)
    offset: int | None = Field(default=None, ge=0)
