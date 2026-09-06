"""Field type and id of the session dependencies table."""

from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = ("SESSION_DEPENDENCY_FIELD_TYPE", "SessionDependencyID")

SESSION_DEPENDENCY_FIELD_TYPE = FieldType("session_dependency")


class SessionDependencyID(FieldIdentifier):
    """One edge of the session dependency graph, owned by the waiting session."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return SESSION_DEPENDENCY_FIELD_TYPE
