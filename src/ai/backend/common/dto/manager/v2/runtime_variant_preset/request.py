from __future__ import annotations

from typing import Self
from uuid import UUID

from pydantic import Field, model_validator

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    VALUE_TYPE_VALIDATORS,
    PresetTarget,
    PresetValueType,
    RuntimeVariantPresetOrderField,
    UIOption,
)


class CreateRuntimeVariantPresetInput(BaseRequestModel):
    runtime_variant_id: UUID = Field(
        description="ID of the runtime variant this preset belongs to."
    )
    name: str = Field(min_length=1, max_length=256, description="Preset name.")
    description: str | None = Field(default=None, description="Description.")
    preset_target: PresetTarget = Field(description="Target: env or args.")
    value_type: PresetValueType = Field(description="Value type: str, int, float, bool, flag.")
    default_value: str | None = Field(default=None, max_length=512, description="Default value.")
    key: str = Field(min_length=1, max_length=256, description="Env key or args flag.")
    required: bool = Field(
        default=False,
        description="Whether this preset param must be supplied on a deployment revision.",
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
    name: str | None = Field(default=None, min_length=1, max_length=256)
    description: str | Sentinel | None = Field(default=SENTINEL)
    rank: int | None = Field(default=None, ge=0)
    preset_target: PresetTarget | None = Field(default=None)
    value_type: PresetValueType | None = Field(default=None)
    default_value: str | Sentinel | None = Field(default=SENTINEL)
    key: str | None = Field(default=None, min_length=1, max_length=256)
    required: bool | None = Field(
        default=None, description="Toggle required flag; None = no change."
    )
    category: str | Sentinel | None = Field(default=SENTINEL)
    display_name: str | Sentinel | None = Field(default=SENTINEL)
    ui_option: UIOption | Sentinel | None = Field(default=SENTINEL)

    @model_validator(mode="after")
    def validate_flag_requires_args(self) -> Self:
        if (
            self.value_type == PresetValueType.FLAG
            and self.preset_target is not None
            and self.preset_target != PresetTarget.ARGS
        ):
            raise ValueError("value_type 'flag' is only valid with preset_target 'args'.")
        return self

    @model_validator(mode="after")
    def validate_default_value(self) -> Self:
        if self.value_type is None or self.default_value is SENTINEL or self.default_value is None:
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
