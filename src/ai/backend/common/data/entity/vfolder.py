"""Entity type and id of the vfolders table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("VFOLDER_ENTITY_TYPE", "VFolderUUID")

VFOLDER_ENTITY_TYPE = EntityType("vfolder")


class VFolderUUID(EntityIdentifier):
    """A vfolder's entity id.

    Named ``VFolderUUID`` because ``common/types.py`` already has a composite
    ``VFolderID`` pairing a quota scope with a folder id.
    """

    @override
    def entity_type(self) -> EntityType:
        return VFOLDER_ENTITY_TYPE
