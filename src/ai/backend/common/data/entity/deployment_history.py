"""Field type and id of the deployment history table."""

from typing import override

from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = ("DeploymentHistoryFieldType", "DeploymentHistoryID")


class DeploymentHistoryFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "deployment_history"

    @override
    @classmethod
    def description(cls) -> str:
        return "One state change of a deployment."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return DeploymentEntityType


class DeploymentHistoryID(FieldIdentifier):
    """A deployment history row's id."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return DeploymentHistoryFieldType()
