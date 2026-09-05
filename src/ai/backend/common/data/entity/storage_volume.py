"""Entity type and id of the storage_volumes table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "STORAGE_VOLUME_ENTITY_TYPE",
    "StorageVolumeID",
)


STORAGE_VOLUME_ENTITY_TYPE = EntityType("storage_volume")


class StorageVolumeID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return STORAGE_VOLUME_ENTITY_TYPE
