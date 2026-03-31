from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.resource import ModelCardConflict
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.model_card.types import MinResourceSpec
from ai.backend.manager.repositories.base.creator import CreatorSpec
from ai.backend.manager.repositories.base.types import IntegrityErrorCheck


@dataclass
class ModelCardCreatorSpec(CreatorSpec[ModelCardRow]):
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
    min_resource: MinResourceSpec | None
    readme: str | None

    @property
    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return (
            IntegrityErrorCheck(
                violation_type=UniqueConstraintViolationError,
                error=ModelCardConflict(f"Duplicate model card name: {self.name}"),
            ),
        )

    @override
    def build_row(self) -> ModelCardRow:
        row = ModelCardRow()
        row.name = self.name
        row.vfolder = self.vfolder_id
        row.domain = self.domain
        row.project = self.project_id
        row.creator = self.creator_id
        row.author = self.author
        row.title = self.title
        row.model_version = self.model_version
        row.description = self.description
        row.task = self.task
        row.category = self.category
        row.architecture = self.architecture
        row.framework = self.framework
        row.label = self.label
        row.license = self.license
        row.min_resource = self.min_resource
        row.readme = self.readme
        return row
