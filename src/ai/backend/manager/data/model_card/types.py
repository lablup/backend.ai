from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import override
from uuid import UUID

from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.common.data.entity.types import EntityData
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.common.types import QuotaScopeID


@dataclass(frozen=True)
class ResourceRequirementEntry:
    """A single resource requirement entry (slot_name → min_quantity)."""

    slot_name: str
    min_quantity: str


@dataclass(frozen=True)
class ModelCardData(EntityData):
    id: UUID
    name: str
    vfolder_id: VFolderUUID
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
    readme: str | None
    access_level: str
    created_at: datetime
    updated_at: datetime | None

    @override
    def entity_id(self) -> ModelCardID:
        return ModelCardID(self.id)


@dataclass(frozen=True)
class BulkModelCardDeleteFailure:
    """Error info for a single failed model card delete inside a bulk operation."""

    card_id: UUID
    message: str


@dataclass(frozen=True)
class BulkModelCardDeleteResultData:
    """Result of bulk model card delete operation, with partial-failure support."""

    successes: list[UUID]
    failures: list[BulkModelCardDeleteFailure]


@dataclass(frozen=True)
class VFolderScanData:
    """Minimal vfolder data needed for model card scan."""

    id: VFolderUUID
    name: str
    host: str
    quota_scope_id: QuotaScopeID
    unmanaged_path: str | None
    domain_name: str
    project_id: UUID
