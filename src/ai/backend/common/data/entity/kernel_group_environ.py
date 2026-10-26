from typing import override

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = (
    "KernelGroupEnvironFieldType",
    "KernelGroupEnvironID",
)


class KernelGroupEnvironFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "kernel_group_environ"

    @override
    @classmethod
    def description(cls) -> str:
        return "One environment variable of a kernel group."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return SessionEntityType


class KernelGroupEnvironID(FieldIdentifier):
    """One environment variable of a kernel group."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return KernelGroupEnvironFieldType()
