from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "STORAGE_NAMESPACE_ENTITY_TYPE",
    "StorageNamespaceID",
)


# Raw string mirroring the RBAC-managed EntityType.STORAGE_NAMESPACE value.
STORAGE_NAMESPACE_ENTITY_TYPE = EntityType("storage_namespace")


class StorageNamespaceID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return STORAGE_NAMESPACE_ENTITY_TYPE
