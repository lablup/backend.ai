from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "OBJECT_STORAGE_ENTITY_TYPE",
    "ObjectStorageID",
)


# Raw string mirroring the RBAC-managed EntityType.OBJECT_STORAGE value.
OBJECT_STORAGE_ENTITY_TYPE = EntityType("object_storage")


class ObjectStorageID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return OBJECT_STORAGE_ENTITY_TYPE
