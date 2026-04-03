"""UpserterSpec for model card scan upsert operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.manager.data.model_card.types import ResourceRequirementEntry
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.repositories.base.upserter import UpserterSpec


@dataclass
class ModelCardScanUpserterSpec(UpserterSpec[ModelCardRow]):
    """Upsert spec for scan operation.

    Conflict key: (name, domain, project) via uq_model_cards_name_domain_project.
    On conflict: update metadata + vfolder, preserve creator.
    """

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

    @property
    @override
    def row_class(self) -> type[ModelCardRow]:
        return ModelCardRow

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "vfolder": self.vfolder_id,
            "domain": self.domain,
            "project": self.project_id,
            "creator": self.creator_id,
            "author": self.author,
            "title": self.title,
            "model_version": self.model_version,
            "description": self.description,
            "task": self.task,
            "category": self.category,
            "architecture": self.architecture,
            "framework": self.framework,
            "label": self.label,
            "license": self.license,
            "readme": self.readme,
            "access_level": self.access_level,
        }

    @override
    def build_update_values(self) -> dict[str, Any]:
        return {
            "vfolder": self.vfolder_id,
            "author": self.author,
            "title": self.title,
            "model_version": self.model_version,
            "description": self.description,
            "task": self.task,
            "category": self.category,
            "architecture": self.architecture,
            "framework": self.framework,
            "label": self.label,
            "license": self.license,
            "readme": self.readme,
            "access_level": self.access_level,
        }
