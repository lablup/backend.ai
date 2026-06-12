from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field

from ai.backend.common.api_handlers import SENTINEL, BaseRequestModel, Sentinel
from ai.backend.common.config import DEFAULT_SHELL, ModelDefinition, PreStartAction
from ai.backend.common.dto.manager.query import StringFilter, UUIDFilter
from ai.backend.common.dto.manager.v2.common import (
    EnvironmentVariableEntryInput,
    OrderDirection,
    ResourceSlotEntryInput,
)
from ai.backend.common.dto.manager.v2.deployment.request import DeploymentStrategyInput
from ai.backend.common.dto.manager.v2.deployment_revision_preset.types import (
    DeploymentRevisionPresetOrderField,
)
from ai.backend.common.dto.manager.v2.resource_slot.types import ResourceOptsEntryDTO
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID


class PresetValueInput(BaseRequestModel):
    preset_id: UUID = Field(description="Runtime variant preset ID.")
    value: str = Field(description="Value for this preset.")


class PresetModelHealthCheckInput(BaseRequestModel):
    enable: bool = Field(
        default=False,
        description="Whether the route is health-checked. When false the route activates "
        "immediately and the remaining fields are ignored.",
    )
    interval: float = Field(default=10.0, description="Interval in seconds between health checks.")
    path: str = Field(default="/health", description="Path to check for health status.")
    max_retries: int = Field(default=10, description="Maximum number of retries for health check.")
    max_wait_time: float = Field(
        default=15.0, description="Maximum time in seconds to wait for a health check response."
    )
    expected_status_code: int = Field(
        default=200, gt=100, description="Expected HTTP status code for a healthy response."
    )
    initial_delay: float = Field(
        default=1800.0, ge=0, description="Initial delay in seconds before the first health check."
    )


class PresetModelMetadataInput(BaseRequestModel):
    author: str | None = Field(default=None, description="Author of the model.")
    title: str | None = Field(default=None, description="Title of the model.")
    version: str | None = Field(default=None, description="Version of the model.")
    created: str | None = Field(default=None, description="Creation date of the model.")
    last_modified: str | None = Field(default=None, description="Last modified date of the model.")
    description: str | None = Field(default=None, description="Description of the model.")
    task: str | None = Field(default=None, description="Task type of the model.")
    category: str | None = Field(default=None, description="Category of the model.")
    architecture: str | None = Field(default=None, description="Architecture of the model.")
    framework: list[str] | None = Field(default=None, description="Frameworks used by the model.")
    label: list[str] | None = Field(default=None, description="Labels for the model.")
    license: str | None = Field(default=None, description="License of the model.")
    min_resource: dict[str, Any] | None = Field(
        default=None, description="Minimum resource requirements for the model."
    )


class PresetModelServiceConfigInput(BaseRequestModel):
    pre_start_actions: list[PreStartAction] = Field(
        default_factory=list,
        description="Pre-start actions to execute before starting the model service. May be empty.",
    )
    start_command: list[str] = Field(description="Command to start the model service.")
    shell: str = Field(default=DEFAULT_SHELL, description="Shell configured for the model service.")
    port: int = Field(
        gt=1, description="Port number for the model service. Must be greater than 1."
    )
    health_check: PresetModelHealthCheckInput | None = Field(
        default=None, description="Health check configuration for the model service."
    )


class PresetModelConfigInput(BaseRequestModel):
    name: str = Field(min_length=1, description="Name of the model.")
    model_path: str = Field(min_length=1, description="Path to the model file.")
    service: PresetModelServiceConfigInput = Field(
        description="Configuration for the model service."
    )
    metadata: PresetModelMetadataInput | None = Field(
        default=None, description="Metadata about the model."
    )


class PresetModelDefinitionInput(BaseRequestModel):
    models: list[PresetModelConfigInput] = Field(
        min_length=1,
        max_length=1,
        description="List of models in the model definition. Exactly one model is supported.",
    )


class CreateDeploymentRevisionPresetInput(BaseRequestModel):
    runtime_variant_id: RuntimeVariantID = Field(
        description="ID of the runtime variant this preset belongs to."
    )
    name: str = Field(min_length=1, max_length=256, description="Preset name.")
    description: str | None = Field(default=None, description="Description.")
    image_id: ImageID = Field(description="Container image UUID.")
    model_definition: PresetModelDefinitionInput | None = Field(
        default=None,
        description="Model definition configuration. Optional, but when provided it must be "
        "fully populated (non-empty models, each with name/model_path/service).",
    )
    resource_slots: list[ResourceSlotEntryInput] | None = Field(
        default=None, description="Resource slot allocations."
    )
    resource_opts: list[ResourceOptsEntryDTO] | None = Field(
        default=None, description="Additional resource options."
    )
    cluster_mode: str = Field(max_length=16, description="Cluster mode.")
    cluster_size: int = Field(ge=1, description="Cluster size.")
    startup_command: str | None = Field(default=None, description="Startup command.")
    bootstrap_script: str | None = Field(default=None, description="Bootstrap script.")
    environ: list[EnvironmentVariableEntryInput] | None = Field(
        default=None, description="Environment variables."
    )
    preset_values: list[PresetValueInput] | None = Field(
        default=None, description="Preset values from runtime variant presets."
    )
    open_to_public: bool | None = Field(
        default=None,
        description="Default open_to_public for deployments created from this preset.",
    )
    replica_count: int = Field(
        ge=0,
        description="Default replica count for deployments created from this preset.",
    )
    revision_history_limit: int | None = Field(
        default=None,
        ge=0,
        description="Default revision history limit for deployments created from this preset.",
    )
    deployment_strategy: DeploymentStrategyInput = Field(
        description="Default deployment strategy (rolling or blue-green) for "
        "deployments created from this preset.",
    )


class UpdateDeploymentRevisionPresetInput(BaseRequestModel):
    id: UUID = Field(description="Preset ID.")
    runtime_variant_id: RuntimeVariantID | None = Field(default=None)
    name: str | None = Field(default=None, min_length=1, max_length=256)
    description: str | Sentinel | None = Field(default=SENTINEL)
    rank: int | None = Field(default=None, ge=0)
    image_id: ImageID | Sentinel | None = Field(default=SENTINEL)
    model_definition: ModelDefinition | Sentinel | None = Field(default=SENTINEL)
    resource_slots: list[ResourceSlotEntryInput] | None = Field(default=None)
    resource_opts: list[ResourceOptsEntryDTO] | None = Field(default=None)
    cluster_mode: str | None = Field(default=None, max_length=16)
    cluster_size: int | None = Field(default=None, ge=1)
    startup_command: str | Sentinel | None = Field(default=SENTINEL)
    bootstrap_script: str | Sentinel | None = Field(default=SENTINEL)
    environ: list[EnvironmentVariableEntryInput] | None = Field(default=None)
    preset_values: list[PresetValueInput] | None = Field(default=None)
    open_to_public: bool | Sentinel | None = Field(default=SENTINEL)
    replica_count: int | Sentinel | None = Field(default=SENTINEL, ge=0)
    revision_history_limit: int | Sentinel | None = Field(default=SENTINEL, ge=0)
    deployment_strategy: DeploymentStrategyInput | Sentinel | None = Field(default=SENTINEL)


class DeploymentRevisionPresetFilter(BaseRequestModel):
    id: UUIDFilter | None = Field(default=None, description="Filter by preset ID.")
    name: StringFilter | None = Field(default=None)
    runtime_variant_id: UUIDFilter | None = Field(default=None)
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
