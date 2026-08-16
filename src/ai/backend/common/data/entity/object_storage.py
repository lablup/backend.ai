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
    @classmethod
    def entity_type(cls) -> EntityType:
        return OBJECT_STORAGE_ENTITY_TYPE
