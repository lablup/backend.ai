"""Field type and id of the session scheduling history table."""

from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = ("SESSION_SCHEDULING_HISTORY_FIELD_TYPE", "SessionSchedulingHistoryID")

SESSION_SCHEDULING_HISTORY_FIELD_TYPE = FieldType("session_scheduling_history")


class SessionSchedulingHistoryID(FieldIdentifier):
    """A session scheduling history row's id."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return SESSION_SCHEDULING_HISTORY_FIELD_TYPE
