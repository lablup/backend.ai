from typing import NewType, override

from ai.backend.common.data.entity.resource_slot import RESOURCE_SLOT_TYPE_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "ResourceSlotName",
    "ResourceSlotTypeUUID",
)


ResourceSlotName = NewType("ResourceSlotName", str)


class ResourceSlotTypeUUID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return RESOURCE_SLOT_TYPE_ENTITY_TYPE
