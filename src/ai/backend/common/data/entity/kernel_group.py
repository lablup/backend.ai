"""Id and natural key of the kernel_groups table.

A kernel group is one role of a session and carries no membership of its own, so its
id is a field identifier: what a group belongs to is knowable only through that session.
"""

from typing import override

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
    NaturalKey,
)

__all__ = (
    "KernelGroupID",
    "KernelGroupRole",
)


class KernelGroupFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "kernel_group"

    @override
    @classmethod
    def description(cls) -> str:
        return "One role of a session, sharing one execution spec across its kernels."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return SessionEntityType


class KernelGroupID(FieldIdentifier):
    """A kernel group row's id."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return KernelGroupFieldType()


class KernelGroupRole(NaturalKey):
    """The role label of a kernel group, unique within its session."""

    @override
    @classmethod
    def key_name(cls) -> str:
        return "kernel_group_role"
