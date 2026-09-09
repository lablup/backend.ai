"""Field type and id of the replica_groups table."""

from typing import override

from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = ("ReplicaGroupFieldType", "ReplicaGroupID")


class ReplicaGroupFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "replica_group"

    @override
    @classmethod
    def description(cls) -> str:
        return "A set of replicas of a deployment that share a revision."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return DeploymentEntityType


class ReplicaGroupID(FieldIdentifier):
    """A replica group's id.

    A group belongs to one deployment and is authorized through it, so the
    deployment owns the row.
    """

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return ReplicaGroupFieldType()
