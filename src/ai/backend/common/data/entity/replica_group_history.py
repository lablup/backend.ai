"""Entity type and id of the replica group history table."""

from typing import override

from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = ("ReplicaGroupHistoryFieldType", "ReplicaGroupHistoryID")


class ReplicaGroupHistoryFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "replica_group_history"

    @override
    @classmethod
    def description(cls) -> str:
        return "One state change of a replica group."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return DeploymentEntityType


class ReplicaGroupHistoryID(FieldIdentifier):
    """A replica group history row's id."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return ReplicaGroupHistoryFieldType()
