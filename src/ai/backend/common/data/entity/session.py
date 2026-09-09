from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType, ScopeType

__all__ = (
    "SessionEntityType",
    "SESSION_SCOPE_TYPE",
    "SessionID",
)


class SessionEntityType(EntityType):
    @override
    @classmethod
    def name(cls) -> str:
        return "session"

    @override
    @classmethod
    def description(cls) -> str:
        return "A compute session made of one or more kernels."


SESSION_SCOPE_TYPE = ScopeType(SessionEntityType())


class SessionID(EntityIdentifier):
    @override
    def entity_type(self) -> EntityType:
        return SessionEntityType()
