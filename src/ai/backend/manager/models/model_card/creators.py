from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import override
from uuid import UUID

from ai.backend.common.data.entity.model_card import MODEL_CARD_ENTITY_TYPE
from ai.backend.common.data.entity.project import PROJECT_ENTITY_TYPE
from ai.backend.common.data.entity.types import ScopeRef, ScopeType
from ai.backend.common.identifier.scope import ScopeID
from ai.backend.common.identifier.vfolder import VFolderUUID
from ai.backend.manager.data.model_card.types import ModelCardData, ResourceRequirementEntry
from ai.backend.manager.errors.repository import UniqueConstraintViolationError
from ai.backend.manager.errors.resource import ModelCardConflict
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.resource_slot.row import ModelCardResourceRequirementRow
from ai.backend.manager.models.specs.creator import EntityCreator
from ai.backend.manager.models.specs.types import IntegrityErrorCheck

_PROJECT_SCOPE = ScopeType(PROJECT_ENTITY_TYPE)
_MODEL_CARD_SCOPE = ScopeType(MODEL_CARD_ENTITY_TYPE)


@dataclass
class ModelCardCreator(EntityCreator[ModelCardRow, ModelCardData]):
    """Creator for a model card.

    A card is its own scope and joins the model-store project it is registered in,
    which is what the RBAC element reference used to say from the call site.
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
    def scope_type(self) -> ScopeType:
        return _MODEL_CARD_SCOPE

    @override
    def scope_id(self, row: ModelCardRow) -> ScopeID:
        return row.id

    @override
    def member_of(self, row: ModelCardRow) -> Collection[ScopeRef]:
        return (ScopeRef(scope_type=_PROJECT_SCOPE, scope_id=self.project_id),)

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

    def build_requirement_rows(self, card_id: UUID) -> list[ModelCardResourceRequirementRow]:
        """The requirement rows this card owns, once the card has an id."""
        return [
            ModelCardResourceRequirementRow(
                model_card_id=card_id,
                slot_name=entry.slot_name,
                min_quantity=entry.min_quantity,
            )
            for entry in (self.min_resource or [])
        ]

    @override
    def to_data(self, row: ModelCardRow) -> ModelCardData:
        return row.to_data()
