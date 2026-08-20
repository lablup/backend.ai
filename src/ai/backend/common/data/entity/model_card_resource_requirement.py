from typing import override

from ai.backend.common.data.entity.model_card import MODEL_CARD_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType, FieldIdentifier, FieldType

__all__ = ("ModelCardResourceRequirementID",)


MODEL_CARD_RESOURCE_REQUIREMENT_FIELD_TYPE = FieldType("model_card_resource_requirement")


class ModelCardResourceRequirementID(FieldIdentifier):
    """One slot a model card requires."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return MODEL_CARD_RESOURCE_REQUIREMENT_FIELD_TYPE

    @override
    @classmethod
    def owner_entity_type(cls) -> EntityType:
        return MODEL_CARD_ENTITY_TYPE
