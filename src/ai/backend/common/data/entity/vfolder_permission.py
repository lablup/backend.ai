"""Field type and id of the vfolder_permissions table."""

from typing import override

from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)
from ai.backend.common.data.entity.vfolder import VFolderEntityType

__all__ = ("VFolderPermissionFieldType", "VFolderPermissionID")


class VFolderPermissionFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "vfolder_permission"

    @override
    @classmethod
    def description(cls) -> str:
        return "One user's permission on a vfolder."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return VFolderEntityType


class VFolderPermissionID(FieldIdentifier):
    """A vfolder permission row's id."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return VFolderPermissionFieldType()
