from typing import override

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = ("KernelGroupVFolderMountID",)


class KernelGroupVFolderMountFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "kernel_group_vfolder_mount"

    @override
    @classmethod
    def description(cls) -> str:
        return "One vfolder mount of a kernel group."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return SessionEntityType


class KernelGroupVFolderMountID(FieldIdentifier):
    """One vfolder mount of a kernel group."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return KernelGroupVFolderMountFieldType()
