"""Field type and id of the routings table."""

from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = ("REPLICA_FIELD_TYPE", "ReplicaID")

REPLICA_FIELD_TYPE = FieldType("replica")


class ReplicaID(FieldIdentifier):
    """A replica's id.

    A replica serves one deployment and is authorized through it, so the deployment
    owns the row and the replica declares no scope of its own.
    """

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return REPLICA_FIELD_TYPE
