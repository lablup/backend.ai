"""Field type and id of the session dependencies table."""

from typing import override

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = ("SessionDependencyFieldType", "SessionDependencyID")


class SessionDependencyFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "session_dependency"

    @override
    @classmethod
    def description(cls) -> str:
        return "One session another session waits on."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return SessionEntityType


class SessionDependencyID(FieldIdentifier):
    """One edge of the session dependency graph, owned by the waiting session."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return SessionDependencyFieldType()
