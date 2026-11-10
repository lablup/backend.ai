"""Field type and id of the session scheduling history table."""

from typing import override

from ai.backend.common.data.entity.session import SessionEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = ("SessionSchedulingHistoryFieldType", "SessionSchedulingHistoryID")


class SessionSchedulingHistoryFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "session_scheduling_history"

    @override
    @classmethod
    def description(cls) -> str:
        return (
            "One run of a session scheduling handler, recording any status change and its result."
        )

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return SessionEntityType


class SessionSchedulingHistoryID(FieldIdentifier):
    """A session scheduling history row's id."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return SessionSchedulingHistoryFieldType()
