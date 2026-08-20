from typing import override

from ai.backend.common.data.entity.session import SESSION_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType, FieldIdentifier, FieldType

__all__ = ("ResourceAllocationID",)


RESOURCE_ALLOCATION_FIELD_TYPE = FieldType("resource_allocation")


class ResourceAllocationID(FieldIdentifier):
    """One slot's amount allocated to one kernel of a session.

    Owned by the session: a kernel is how a session is spread over agents, and the
    allocation is answered for by the session the caller named."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return RESOURCE_ALLOCATION_FIELD_TYPE

    @override
    @classmethod
    def owner_entity_type(cls) -> EntityType:
        return SESSION_ENTITY_TYPE
