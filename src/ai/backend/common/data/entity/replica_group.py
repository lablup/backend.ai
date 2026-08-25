"""Field type and id of the replica_groups table."""

from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = ("REPLICA_GROUP_FIELD_TYPE", "ReplicaGroupID")

REPLICA_GROUP_FIELD_TYPE = FieldType("replica_group")


class ReplicaGroupID(FieldIdentifier):
    """A replica group's id.

    A group belongs to one deployment and is authorized through it, so the
    deployment owns the row.
    """

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return REPLICA_GROUP_FIELD_TYPE
