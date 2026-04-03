from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from ai.backend.common.types import QuotaScopeID


@dataclass(frozen=True)
class ResourceRequirementEntry:
    """A single resource requirement entry (slot_name → min_quantity)."""

    slot_name: str
    min_quantity: str


@dataclass(frozen=True)
class ModelCardData:
    id: UUID
    name: str
    vfolder_id: UUID
    domain: str
    project_id: UUID
    creator_id: UUID
    author: str | None
    title: str | None
    model_version: str | None
    description: str | None
    task: str | None
    category: str | None
    architecture: str | None
    framework: list[str]
    label: list[str]
    license: str | None
    min_resource: list[ResourceRequirementEntry]
    readme: str | None
    access_level: str
    created_at: datetime
    updated_at: datetime | None


@dataclass(frozen=True)
class VFolderScanData:
    """Minimal vfolder data needed for model card scan."""

    id: UUID
    name: str
    host: str
    quota_scope_id: QuotaScopeID
    unmanaged_path: str | None
    domain_name: str
    project_id: UUID
