from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.model_card import ModelCardID
from ai.backend.common.data.entity.model_card_resource_requirement import (
    ModelCardResourceRequirementID,
)
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.common.data.entity.user import UserID
from ai.backend.common.data.entity.vfolder import VFolderUUID
from ai.backend.manager.data.model_card.types import (
    ModelCardData,
    ModelCardResourceRequirementData,
    ResourceRequirementEntry,
)
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.resource import ModelCardConflict
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.resource_slot.row import ModelCardResourceRequirementRow
from ai.backend.manager.models.specs.creator import EntityCreator, FieldCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck


@dataclass
class ModelCardCreator(EntityCreator[ModelCardRow, ModelCardData]):
    """Creator for a model card.

    A card is its own scope and joins the model-store project it is registered in,
    which is what the RBAC element reference used to say from the call site.
    """

    name: str
    vfolder_id: VFolderUUID
    domain: str
    project_id: ProjectID
    creator_id: UserID
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

    @override
    def entity_id(self, row: ModelCardRow) -> ModelCardID:
        return ModelCardID(row.id)

    @override
    def created_in(self, row: ModelCardRow) -> Collection[EntityIdentifier]:
        return (ProjectID(self.project_id),)

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
        row.readme = self.readme
        row.access_level = self.access_level
        return row

    @override
    def to_data(self, row: ModelCardRow) -> ModelCardData:
        return row.to_data()


@dataclass
class ModelCardResourceRequirementCreator(
    FieldCreator[ModelCardID, ModelCardResourceRequirementRow, ModelCardResourceRequirementData]
):
    """Insert one minimum slot quantity of the card that owns it."""

    entry: ResourceRequirementEntry

    @override
    def field_id(self, row: ModelCardResourceRequirementRow) -> ModelCardResourceRequirementID:
        return row.id

    @override
    def integrity_error_checks(self) -> Sequence[IntegrityErrorCheck]:
        return ()

    @override
    def build_row(self, owner_id: ModelCardID) -> ModelCardResourceRequirementRow:
        return ModelCardResourceRequirementRow(
            model_card_id=owner_id,
            slot_name=self.entry.slot_name,
            min_quantity=self.entry.min_quantity,
        )

    @override
    def to_data(self, row: ModelCardResourceRequirementRow) -> ModelCardResourceRequirementData:
        return row.to_data()
