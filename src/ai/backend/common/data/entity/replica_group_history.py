"""Entity type and id of the replica group history table."""

from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = ("REPLICA_GROUP_HISTORY_FIELD_TYPE", "ReplicaGroupHistoryID")

REPLICA_GROUP_HISTORY_FIELD_TYPE = FieldType("replica_group_history")


class ReplicaGroupHistoryID(FieldIdentifier):
    """A replica group history row's id."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return REPLICA_GROUP_HISTORY_FIELD_TYPE
