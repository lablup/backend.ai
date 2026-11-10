from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "ModelCardEntityType",
    "ModelCardID",
)


class ModelCardEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "model_card"

    @override
    @classmethod
    def description(cls) -> str:
        return "A description of a model kept in a vfolder."


class ModelCardID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return ModelCardEntityType()
