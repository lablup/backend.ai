from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "MODEL_CARD_ENTITY_TYPE",
    "ModelCardID",
)


# Raw string mirroring the RBAC-managed EntityType.MODEL_CARD value.
MODEL_CARD_ENTITY_TYPE = EntityType("model_card")


class ModelCardID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return MODEL_CARD_ENTITY_TYPE
