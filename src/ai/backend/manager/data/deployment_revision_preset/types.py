from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ai.backend.common.config import ModelDefinition
from ai.backend.common.data.model_deployment.types import DeploymentStrategy
from ai.backend.common.identifier.deployment_preset import DeploymentPresetID
from ai.backend.common.identifier.image import ImageID
from ai.backend.common.identifier.runtime_variant import RuntimeVariantID


@dataclass(frozen=True)
class PresetValueData:
    preset_id: DeploymentPresetID
    value: str


@dataclass(frozen=True)
class ResourceSlotEntryData:
    resource_type: str
    quantity: str


@dataclass(frozen=True)
class ResourceOptsEntryData:
    name: str
    value: str


@dataclass(frozen=True)
class EnvironEntryData:
    key: str
    value: str


@dataclass(frozen=True)
class DeploymentRevisionPresetData:
    id: DeploymentPresetID
    runtime_variant_id: RuntimeVariantID
    name: str
    description: str | None
    rank: int
    image_id: ImageID
    model_definition: ModelDefinition | None
    resource_opts: list[ResourceOptsEntryData]
    cluster_mode: str
    cluster_size: int
    startup_command: str | None
    bootstrap_script: str | None
    environ: list[EnvironEntryData]
    preset_values: list[PresetValueData]
    replica_count: int
    deployment_strategy: DeploymentStrategy
    deployment_strategy_spec: dict[str, Any]
    # Deployment-level preset fields with system defaults at deployment-create
    # time; ``None`` means the preset does not specify this value.
    open_to_public: bool | None = None
    revision_history_limit: int | None = None
    created_at: datetime = field(default=None)  # type: ignore[assignment]
    updated_at: datetime | None = None
