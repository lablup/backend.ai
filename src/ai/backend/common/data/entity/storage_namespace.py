from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "StorageNamespaceEntityType",
    "StorageNamespaceID",
)


class StorageNamespaceEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "storage_namespace"

    @override
    @classmethod
    def description(cls) -> str:
        return "A named space in a storage backend that holds artifacts."


class StorageNamespaceID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return StorageNamespaceEntityType()
