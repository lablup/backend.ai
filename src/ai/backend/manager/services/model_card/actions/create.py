from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import override

from ai.backend.common.data.entity.model_card import ModelCardEntityType
from ai.backend.common.data.entity.project import ProjectID
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.manager.actions.v2.ops.base import CreateEntityWithFieldsOpsAction
from ai.backend.manager.data.model_card.types import (
    ModelCardData,
    ModelCardResourceRequirementData,
    ResourceRequirementEntry,
)
from ai.backend.manager.models.model_card.creators import (
    ModelCardCreator,
    ModelCardResourceRequirementCreator,
)
from ai.backend.manager.models.model_card.row import ModelCardRow
from ai.backend.manager.models.resource_slot.row import ModelCardResourceRequirementRow


@dataclass(frozen=True)
class CreateModelCardAction(
    CreateEntityWithFieldsOpsAction[
        ModelCardRow,
        ModelCardData,
        ModelCardResourceRequirementRow,
        ModelCardResourceRequirementData,
    ]
):
    """Register a model card in a project, with the minimum resources it declares."""

    creator: ModelCardCreator
    min_resource: Sequence[ResourceRequirementEntry]

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return ModelCardEntityType()

    @override
    def scope_targets(self) -> Sequence[EntityIdentifier]:
        return (ProjectID(self.creator.project_id),)

    @override
    @classmethod
    def action_name(cls) -> str:
        return "create_model_card"

    @override
    def to_creator(self) -> ModelCardCreator:
        return self.creator

    @override
    def to_field_creators(self) -> Sequence[ModelCardResourceRequirementCreator]:
        return [ModelCardResourceRequirementCreator(entry=entry) for entry in self.min_resource]
