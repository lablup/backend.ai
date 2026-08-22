from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "VFSStorageID",
    "VFS_STORAGE_ENTITY_TYPE",
)


# Raw string mirroring the RBAC-managed EntityType.VFS_STORAGE value.
VFS_STORAGE_ENTITY_TYPE = EntityType("vfs_storage")


class VFSStorageID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return VFS_STORAGE_ENTITY_TYPE
