"""Upsert specs for model cards."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Any, override
from uuid import UUID

from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.manager.data.model_card.types import ModelCardData, ResourceRequirementEntry
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.specs.types import IntegrityErrorCheck
from ai.backend.manager.models.specs.upserter import EntityUpserter


@dataclass
class ModelCardScanUpserter(EntityUpserter[ModelCardRow, ModelCardData]):
    """Registers one card found by a model-store scan.

    Conflict key: (name, domain, project) via uq_model_cards_name_domain_project.
    On conflict the metadata and the vfolder are updated and the creator is kept.
    ``min_resource`` is not a card column; the caller replaces the normalized
    requirement rows with it after the upsert.
    """

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
    min_resource: list[ResourceRequirementEntry]
    readme: str | None
    access_level: str

    @override
    def entity_id(self, row: ModelCardRow) -> ModelCardID:
        return ModelCardID(row.id)

    @override
    def created_in(self, row: ModelCardRow) -> Collection[EntityIdentifier]:
        return (ProjectID(self.project_id),)

    @override
    def row_class(self) -> type[ModelCardRow]:
        return ModelCardRow

    @override
    def index_elements(self) -> list[str]:
        return ["name", "domain", "project"]

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_insert_values(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "vfolder": self.vfolder_id,
            "domain": self.domain,
            "project": self.project_id,
            "creator": self.creator_id,
            **self.build_update_values(),
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

    @override
    def to_data(self, row: ModelCardRow) -> ModelCardData:
        return row.to_data()
