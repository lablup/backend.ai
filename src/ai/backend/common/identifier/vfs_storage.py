from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType
from ai.backend.common.data.entity.vfs_storage import VFS_STORAGE_ENTITY_TYPE

__all__ = ("VFSStorageID",)


class VFSStorageID(EntityIdentifier):
    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return VFS_STORAGE_ENTITY_TYPE
