"""Field type and id of the vfolder_user_mount_policies table."""

from typing import override

from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)
from ai.backend.common.data.entity.vfolder import VFolderEntityType

__all__ = ("VFolderMountPolicyFieldType", "VFolderMountPolicyID")


class VFolderMountPolicyFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "vfolder_mount_policy"

    @override
    @classmethod
    def description(cls) -> str:
        return "The mount level one user gets on a vfolder, set by the folder's owner."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return VFolderEntityType


class VFolderMountPolicyID(FieldIdentifier):
    """A vfolder user mount policy row's id."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return VFolderMountPolicyFieldType()
