from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = (
    "VFolderAutoMountEntityType",
    "VFolderAutoMountID",
)


class VFolderAutoMountEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "vfolder_auto_mount"

    @override
    @classmethod
    def description(cls) -> str:
        return "A vfolder mounted into every session created in a project."


class VFolderAutoMountID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return VFolderAutoMountEntityType()
