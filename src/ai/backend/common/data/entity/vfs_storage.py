from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "VFSStorageID",
    "VFSStorageEntityType",
)


class VFSStorageEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "vfs_storage"

    @override
    @classmethod
    def description(cls) -> str:
        return "A filesystem backend behind a storage namespace."


class VFSStorageID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return VFSStorageEntityType()
