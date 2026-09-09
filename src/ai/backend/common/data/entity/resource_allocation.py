from typing import override

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = ("ResourceAllocationID",)


class ResourceAllocationFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "resource_allocation"

    @override
    @classmethod
    def description(cls) -> str:
        return "One slot's amount allocated to one kernel of a session."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return SessionEntityType


class ResourceAllocationID(FieldIdentifier):
    """One slot's amount allocated to one kernel of a session.

    Owned by the session: a kernel is how a session is spread over agents, and the
    allocation is answered for by the session the caller named."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return ResourceAllocationFieldType()
