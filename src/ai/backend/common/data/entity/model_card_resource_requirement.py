from typing import override

from ai.backend.common.data.entity.model_card import MODEL_CARD_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType, FieldIdentifier

__all__ = ("ModelCardResourceRequirementID",)


class ModelCardResourceRequirementID(FieldIdentifier):
    """One slot a model card requires."""

    @override
    @classmethod
    def owner_entity_type(cls) -> EntityType:
        return MODEL_CARD_ENTITY_TYPE
