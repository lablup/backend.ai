from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.dto.manager.query import StringFilter
from ai.backend.common.dto.manager.v2.common import OrderDirection, ResourceSlotEntryInput
from ai.backend.common.dto.manager.v2.deployment_revision_preset.types import (
    DeploymentRevisionPresetOrderField,
)


class EnvironEntryInput(BaseRequestModel):
    key: str = Field(description="Environment variable key.")
    value: str = Field(description="Environment variable value.")


class ResourceOptsEntryInput(BaseRequestModel):
    name: str = Field(description="Resource option name (e.g. shmem).")
    value: str = Field(description="Resource option value (e.g. 1g).")


class PresetValueInput(BaseRequestModel):
    preset_id: UUID = Field(description="Runtime variant preset ID.")
    value: str = Field(description="Value for this preset.")


class CreateDeploymentRevisionPresetInput(BaseRequestModel):
    runtime_variant_id: UUID = Field(
        description="ID of the runtime variant this preset belongs to."
    )
    name: str = Field(min_length=1, max_length=256, description="Preset name.")
    description: str | None = Field(default=None, description="Description.")
    image_id: UUID = Field(description="Container image UUID.")
    model_definition: dict[str, Any] | None = Field(
        default=None, description="Model definition configuration."
    )
    resource_slots: list[ResourceSlotEntryInput] | None = Field(
        default=None, description="Resource slot allocations."
    )
    resource_opts: list[ResourceOptsEntryInput] | None = Field(
        default=None, description="Additional resource options."
    )
    cluster_mode: str | None = Field(default=None, max_length=16, description="Cluster mode.")
    cluster_size: int | None = Field(default=None, ge=1, description="Cluster size.")
    startup_command: str | None = Field(default=None, description="Startup command.")
    bootstrap_script: str | None = Field(default=None, description="Bootstrap script.")
    environ: list[EnvironEntryInput] | None = Field(
        default=None, description="Environment variables."
    )
    preset_values: list[PresetValueInput] | None = Field(
        default=None, description="Preset values from runtime variant presets."
    )


class UpdateDeploymentRevisionPresetInput(BaseRequestModel):
    id: UUID = Field(description="Preset ID.")
    name: str | None = Field(default=None, min_length=1, max_length=256)
    description: str | Sentinel | None = Field(default=SENTINEL)
    rank: int | None = Field(default=None, ge=0)
    image_id: UUID | Sentinel | None = Field(default=SENTINEL)
    model_definition: dict[str, Any] | Sentinel | None = Field(default=SENTINEL)
    resource_slots: list[ResourceSlotEntryInput] | None = Field(default=None)
    resource_opts: list[ResourceOptsEntryInput] | None = Field(default=None)
    cluster_mode: str | None = Field(default=None, max_length=16)
    cluster_size: int | None = Field(default=None, ge=1)
    startup_command: str | Sentinel | None = Field(default=SENTINEL)
    bootstrap_script: str | Sentinel | None = Field(default=SENTINEL)
    environ: list[EnvironEntryInput] | None = Field(default=None)
    preset_values: list[PresetValueInput] | None = Field(default=None)


class DeploymentRevisionPresetFilter(BaseRequestModel):
    name: StringFilter | None = Field(default=None)
    runtime_variant_id: UUID | None = Field(default=None)
    AND: list[DeploymentRevisionPresetFilter] | None = Field(default=None)
    OR: list[DeploymentRevisionPresetFilter] | None = Field(default=None)
    NOT: list[DeploymentRevisionPresetFilter] | None = Field(default=None)


DeploymentRevisionPresetFilter.model_rebuild()


class DeploymentRevisionPresetOrder(BaseRequestModel):
    field: DeploymentRevisionPresetOrderField
    direction: OrderDirection = OrderDirection.ASC


class SearchDeploymentRevisionPresetsInput(BaseRequestModel):
    filter: DeploymentRevisionPresetFilter | None = Field(default=None)
    order: list[DeploymentRevisionPresetOrder] | None = Field(default=None)
    first: int | None = Field(default=None, ge=1)
    after: str | None = Field(default=None)
    last: int | None = Field(default=None, ge=1)
    before: str | None = Field(default=None)
    limit: int | None = Field(default=None, ge=1)
    offset: int | None = Field(default=None, ge=0)
