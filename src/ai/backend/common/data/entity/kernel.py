"""Id of the kernels table.

A kernel runs under a session and carries no membership of its own, so its id is a
field identifier: what a kernel belongs to is knowable only through that session.
"""

from typing import override

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = ("KernelID",)


class KernelFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "kernel"

    @override
    @classmethod
    def description(cls) -> str:
        return "One container of a session, placed on one agent."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return SessionEntityType


class KernelID(FieldIdentifier):
    """A kernel row's id."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return KernelFieldType()
