from typing import NewType, override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "RESOURCE_SLOT_TYPE_ENTITY_TYPE",
    "ResourceSlotName",
    "ResourceSlotTypeUUID",
)


# Raw string mirroring the RBAC-managed EntityType.RESOURCE_SLOT_TYPE value.
RESOURCE_SLOT_TYPE_ENTITY_TYPE = EntityType("resource_slot_type")

ResourceSlotName = NewType("ResourceSlotName", str)


class ResourceSlotTypeUUID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RESOURCE_SLOT_TYPE_ENTITY_TYPE
