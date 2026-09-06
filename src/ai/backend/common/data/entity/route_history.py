"""Field type and id of the route history table."""

from typing import override

from ai.backend.common.data.entity.types import FieldIdentifier, FieldType

__all__ = ("ROUTE_HISTORY_FIELD_TYPE", "RouteHistoryID")

ROUTE_HISTORY_FIELD_TYPE = FieldType("route_history")


class RouteHistoryID(FieldIdentifier):
    """A route history row's id."""

    @override
    @classmethod
    def field_type(cls) -> FieldType:
        return ROUTE_HISTORY_FIELD_TYPE
