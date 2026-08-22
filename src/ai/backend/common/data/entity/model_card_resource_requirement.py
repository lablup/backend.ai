from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = ("ModelCardResourceRequirementID",)


MODEL_CARD_RESOURCE_REQUIREMENT_FIELD_TYPE = FieldType("model_card_resource_requirement")


class ModelCardResourceRequirementID(FieldIdentifier):
    """One slot a model card requires."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return MODEL_CARD_RESOURCE_REQUIREMENT_FIELD_TYPE
