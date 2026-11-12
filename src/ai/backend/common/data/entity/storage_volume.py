"""Entity type, id and name of the storage_volumes table."""

from typing import NewType, override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "StorageVolumeEntityType",
    "StorageVolumeID",
    "StorageVolumeName",
)

StorageVolumeName = NewType("StorageVolumeName", str)


class StorageVolumeEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "storage_volume"

    @override
    @classmethod
    def description(cls) -> str:
        return (
            "A volume on a storage backend, identified by the name every service declares it under."
        )


class StorageVolumeID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return StorageVolumeEntityType()
