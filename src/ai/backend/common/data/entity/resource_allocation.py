from typing import override

from ai.backend.common.data.entity.session import SESSION_ENTITY_TYPE
from ai.backend.common.data.entity.types import EntityType, FieldIdentifier

__all__ = ("ResourceAllocationID",)


class ResourceAllocationID(FieldIdentifier):
    """One slot's amount allocated to one kernel of a session.

    Owned by the session: a kernel is how a session is spread over agents, and the
    allocation is answered for by the session the caller named."""

    @override
    @classmethod
    def owner_entity_type(cls) -> EntityType:
        return SESSION_ENTITY_TYPE
