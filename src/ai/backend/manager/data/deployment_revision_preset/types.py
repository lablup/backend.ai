from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class PresetValueData:
    preset_id: UUID
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
    id: UUID
    runtime_variant_id: UUID
    name: str
    description: str | None
    rank: int
    image_id: UUID
    model_definition: dict[str, Any] | None
    resource_slots: list[ResourceSlotEntryData]
    resource_opts: list[ResourceOptsEntryData]
    cluster_mode: str
    cluster_size: int
    startup_command: str | None
    bootstrap_script: str | None
    environ: list[EnvironEntryData]
    preset_values: list[PresetValueData] = field(default_factory=list)
    created_at: datetime = field(default=None)  # type: ignore[assignment]
    updated_at: datetime | None = None
