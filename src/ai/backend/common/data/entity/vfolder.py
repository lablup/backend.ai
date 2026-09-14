"""Entity type and id of the vfolders table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("VFolderEntityType", "VFolderUUID")


class VFolderEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "vfolder"

    @override
    @classmethod
    def description(cls) -> str:
        return "A virtual folder owned by a user or a project."


class VFolderUUID(EntityIdentifier):
    """A vfolder's entity id.

    Named ``VFolderUUID`` because ``common/types.py`` already has a composite
    ``VFolderID`` pairing a quota scope with a folder id.
    """

    @override
    def entity_type(self) -> EntityType:
        return VFolderEntityType()
