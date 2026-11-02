"""Entity type and id of the storage_backends table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "StorageBackendEntityType",
    "StorageBackendID",
)


class StorageBackendEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "storage_backend"

    @override
    @classmethod
    def description(cls) -> str:
        return "A storage appliance a service can reach."


class StorageBackendID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return StorageBackendEntityType()
