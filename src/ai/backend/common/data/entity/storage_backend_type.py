"""Entity type and id of the storage_backend_types table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "StorageBackendTypeEntityType",
    "StorageBackendTypeID",
)


class StorageBackendTypeEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "storage_backend_type"

    @override
    @classmethod
    def description(cls) -> str:
        return "A storage backend implementation a volume can be served by."


class StorageBackendTypeID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return StorageBackendTypeEntityType()
