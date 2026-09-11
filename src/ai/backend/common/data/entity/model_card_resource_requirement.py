from typing import override

from ai.backend.common.data.entity.model_card import ModelCardEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = ("ModelCardResourceRequirementID",)


class ModelCardResourceRequirementFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "model_card_resource_requirement"

    @override
    @classmethod
    def description(cls) -> str:
        return "One resource requirement a model card declares."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return ModelCardEntityType


class ModelCardResourceRequirementID(FieldIdentifier):
    """One slot a model card requires."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return ModelCardResourceRequirementFieldType()
