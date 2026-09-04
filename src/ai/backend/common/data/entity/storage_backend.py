"""Entity type and id of the storage_backends table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "STORAGE_BACKEND_ENTITY_TYPE",
    "StorageBackendID",
)


STORAGE_BACKEND_ENTITY_TYPE = EntityType("storage_backend")


class StorageBackendID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return STORAGE_BACKEND_ENTITY_TYPE
