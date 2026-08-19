"""Entity type and id of the replica group history table."""

from typing import override

from ai.backend.common.data.entity.types import EntityIdentifier, EntityType

__all__ = ("REPLICA_GROUP_HISTORY_ENTITY_TYPE", "ReplicaGroupHistoryID")

REPLICA_GROUP_HISTORY_ENTITY_TYPE = EntityType("replica_group_history")


class ReplicaGroupHistoryID(EntityIdentifier):
    """A replica group history row's id."""

    @override
    @classmethod
    def entity_type(cls) -> EntityType:
        return REPLICA_GROUP_HISTORY_ENTITY_TYPE
