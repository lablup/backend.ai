from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


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
    min_resource: dict[str, str] | None
    readme: str | None
    created_at: datetime
    updated_at: datetime | None
