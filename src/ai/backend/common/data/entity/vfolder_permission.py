"""Field type and id of the vfolder_permissions table."""

from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = ("VFOLDER_PERMISSION_FIELD_TYPE", "VFolderPermissionID")

VFOLDER_PERMISSION_FIELD_TYPE = FieldType("vfolder_permission")


class VFolderPermissionID(FieldIdentifier):
    """A vfolder permission row's id."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return VFOLDER_PERMISSION_FIELD_TYPE
