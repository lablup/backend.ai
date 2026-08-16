from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, NaturalKey

__all__ = (
    "RESOURCE_SLOT_TYPE_ENTITY_TYPE",
    "ResourceSlotName",
    "ResourceSlotTypeUUID",
)


# Raw string mirroring the RBAC-managed EntityType.RESOURCE_SLOT_TYPE value.
RESOURCE_SLOT_TYPE_ENTITY_TYPE = EntityType("resource_slot_type")


class ResourceSlotName(NaturalKey):
    @override
    @classmethod
    def key_name(cls) -> str:
        return "slot_name"


class ResourceSlotTypeUUID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RESOURCE_SLOT_TYPE_ENTITY_TYPE
