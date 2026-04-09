from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel

from .types import PresetTarget, PresetValueType, UIOption


class PresetTargetSpec(BaseResponseModel):
    preset_target: PresetTarget = Field(description="Target: env or args.")
    value_type: PresetValueType = Field(description="Value type: str, int, float, bool, flag.")
    default_value: str | None = Field(default=None, description="Default value.")
    key: str = Field(description="Env key or args flag.")


class RuntimeVariantPresetNode(BaseResponseModel):
    id: UUID = Field(description="Preset ID.")
    runtime_variant_id: UUID = Field(description="Runtime variant ID.")
    name: str = Field(description="Preset name.")
    description: str | None = Field(default=None, description="Description.")
    rank: int = Field(description="Display order rank.")
    target_spec: PresetTargetSpec = Field(description="Preset target specification.")
    category: str | None = Field(default=None, description="UI category group.")
    ui_type: str | None = Field(
        default=None, description="UI type for rendering (slider, number, choice, text)."
    )
    display_name: str | None = Field(default=None, description="UI display name.")
    ui_option: UIOption | None = Field(default=None, description="UI rendering config.")
    created_at: datetime = Field(description="Creation timestamp.")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp.")


class CreateRuntimeVariantPresetPayload(BaseResponseModel):
    preset: RuntimeVariantPresetNode = Field(description="The created preset.")


class UpdateRuntimeVariantPresetPayload(BaseResponseModel):
    preset: RuntimeVariantPresetNode = Field(description="The updated preset.")


class DeleteRuntimeVariantPresetPayload(BaseResponseModel):
    id: UUID = Field(description="ID of the deleted preset.")


class SearchRuntimeVariantPresetsPayload(BaseResponseModel):
    items: list[RuntimeVariantPresetNode] = Field(description="List of presets.")
    total_count: int = Field(description="Total number of matching items.")
    has_next_page: bool = Field(description="Whether there are more items after.")
    has_previous_page: bool = Field(description="Whether there are more items before.")
