"""Field type and id of the route history table."""

from typing import override

from ai.backend.common.data.entity.deployment import DeploymentEntityType
from ai.backend.common.data.entity.types import (
    EntityType,
    FieldIdentifier,
    FieldType,
)

__all__ = ("RouteHistoryFieldType", "RouteHistoryID")


class RouteHistoryFieldType(FieldType):
    @override
    @classmethod
    def name(cls) -> str:
        return "route_history"

    @override
    @classmethod
    def description(cls) -> str:
        return "One routing change recorded for a deployment."

    @override
    @classmethod
    def owner_type(cls) -> type[EntityType]:
        return DeploymentEntityType


class RouteHistoryID(FieldIdentifier):
    """A route history row's id."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return RouteHistoryFieldType()
