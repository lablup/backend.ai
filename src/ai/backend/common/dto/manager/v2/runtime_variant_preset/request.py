from __future__ import annotations

from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection
from ai.backend.common.dto.manager.v2.runtime_variant_preset.types import (
    PresetTarget,
    PresetValueType,
    RuntimeVariantPresetOrderField,
)


class CreateRuntimeVariantPresetInput(BaseRequestModel):
    runtime_variant_id: UUID = Field(
        description="ID of the runtime variant this preset belongs to."
    )
    name: str = Field(min_length=1, max_length=256, description="Preset name.")
    description: str | None = Field(default=None, description="Description.")
    preset_target: PresetTarget = Field(description="Target: env or args.")
    value_type: PresetValueType = Field(description="Value type: str, int, float, bool.")
    default_value: str | None = Field(default=None, max_length=512, description="Default value.")
    key: str = Field(min_length=1, max_length=256, description="Env key or args flag.")


class UpdateRuntimeVariantPresetInput(BaseRequestModel):
    id: UUID = Field(description="Preset ID.")
    name: str | None = Field(default=None, min_length=1, max_length=256)
    description: str | Sentinel | None = Field(default=SENTINEL)
    rank: int | None = Field(default=None, ge=0)
    preset_target: PresetTarget | None = Field(default=None)
    value_type: PresetValueType | None = Field(default=None)
    default_value: str | Sentinel | None = Field(default=SENTINEL)
    key: str | None = Field(default=None, min_length=1, max_length=256)


class RuntimeVariantPresetFilter(BaseRequestModel):
    name: StringFilter | None = Field(default=None)
    runtime_variant_id: UUID | None = Field(default=None)
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
