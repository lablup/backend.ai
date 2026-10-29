"""Field type and id of the session designated agents table."""

from typing import override

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = ("SessionDesignatedAgentFieldType", "SessionDesignatedAgentID")


class SessionDesignatedAgentFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "session_designated_agent"

    @override
    @classmethod
    def description(cls) -> str:
        return "One agent a session designates for its placement."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return SessionEntityType


class SessionDesignatedAgentID(FieldIdentifier):
    """One agent a session designates, owned by the session."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return SessionDesignatedAgentFieldType()
