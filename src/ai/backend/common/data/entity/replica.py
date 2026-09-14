"""Field type and id of the routings table."""

from typing import override

from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = ("ReplicaFieldType", "ReplicaID")


class ReplicaFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "replica"

    @override
    @classmethod
    def description(cls) -> str:
        return "One session serving a deployment, taking a share of its traffic when healthy."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return DeploymentEntityType


class ReplicaID(FieldIdentifier):
    """A replica's id.

    A replica serves one deployment and is authorized through it, so the deployment
    owns the row and the replica declares no scope of its own.
    """

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return ReplicaFieldType()
