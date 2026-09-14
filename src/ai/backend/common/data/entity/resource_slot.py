from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, NaturalKey

__all__ = (
    "ResourceSlotTypeEntityType",
    "ResourceSlotName",
    "ResourceSlotTypeUUID",
)


class ResourceSlotTypeEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "resource_slot_type"

    @override
    @classmethod
    def description(cls) -> str:
        return "A kind of resource an agent can offer."


class ResourceSlotName(NaturalKey):
    @override
    @classmethod
    def key_name(cls) -> str:
        return "slot_name"


class ResourceSlotTypeUUID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return ResourceSlotTypeEntityType()
