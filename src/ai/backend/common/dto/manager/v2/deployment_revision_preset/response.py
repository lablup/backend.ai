from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import BaseResponseModel


class EnvironEntryInfo(BaseResponseModel):
    key: str = Field(description="Environment variable key.")
    value: str = Field(description="Environment variable value.")


class ResourceSlotEntryInfo(BaseResponseModel):
    resource_type: str = Field(description="Resource type name (e.g. cpu, mem).")
    quantity: str = Field(description="Resource quantity as string.")


class ResourceOptsEntryInfo(BaseResponseModel):
    name: str = Field(description="Resource option name (e.g. shmem).")
    value: str = Field(description="Resource option value (e.g. 1g).")


class PresetValueInfo(BaseResponseModel):
    preset_id: UUID = Field(description="Runtime variant preset ID.")
    value: str = Field(description="Value for this preset.")


class PresetResourceAllocation(BaseResponseModel):
    resource_slots: list[ResourceSlotEntryInfo] = Field(
        default_factory=list, description="Resource slot allocations."
    )
    resource_opts: list[ResourceOptsEntryInfo] = Field(
        default_factory=list, description="Additional resource options."
    )


class PresetExecutionSpec(BaseResponseModel):
    image_id: UUID | None = Field(default=None, description="Container image UUID.")
    startup_command: str | None = Field(default=None, description="Startup command.")
    bootstrap_script: str | None = Field(default=None, description="Bootstrap script.")
    environ: list[EnvironEntryInfo] = Field(
        default_factory=list, description="Environment variables."
    )


class PresetClusterSpec(BaseResponseModel):
    cluster_mode: str = Field(description="Cluster mode.")
    cluster_size: int = Field(description="Cluster size.")


class DeploymentRevisionPresetNode(BaseResponseModel):
    id: UUID = Field(description="Preset ID.")
    runtime_variant_id: UUID = Field(description="Runtime variant ID.")
    name: str = Field(description="Preset name.")
    description: str | None = Field(default=None, description="Description.")
    rank: int = Field(description="Display order rank.")
    cluster: PresetClusterSpec = Field(description="Cluster configuration.")
    resource: PresetResourceAllocation = Field(description="Resource allocation.")
    execution: PresetExecutionSpec = Field(description="Execution configuration.")
    model_definition: dict[str, Any] | None = Field(
        default=None, description="Model definition configuration."
    )
    preset_values: list[PresetValueInfo] = Field(default_factory=list, description="Preset values.")
    created_at: datetime = Field(description="Creation timestamp.")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp.")


class CreateDeploymentRevisionPresetPayload(BaseResponseModel):
    preset: DeploymentRevisionPresetNode = Field(description="The created preset.")


class UpdateDeploymentRevisionPresetPayload(BaseResponseModel):
    preset: DeploymentRevisionPresetNode = Field(description="The updated preset.")


class DeleteDeploymentRevisionPresetPayload(BaseResponseModel):
    id: UUID = Field(description="ID of the deleted preset.")


class SearchDeploymentRevisionPresetsPayload(BaseResponseModel):
    items: list[DeploymentRevisionPresetNode] = Field(description="List of presets.")
    total_count: int = Field(description="Total number of matching items.")
    has_next_page: bool = Field(description="Whether there are more items after.")
    has_previous_page: bool = Field(description="Whether there are more items before.")
