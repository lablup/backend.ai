"""Query orders for routing repository."""

from __future__ import annotations

from ai.backend.manager.models.routing import RoutingRow
from ai.backend.manager.repositories.base import QueryOrder


class RouteOrders:
    """Query orders for routes."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RoutingRow.created_at.asc()
        return RoutingRow.created_at.desc()

    @staticmethod
    def status(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RoutingRow.status.asc()
        return RoutingRow.status.desc()

    @staticmethod
    def traffic_ratio(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RoutingRow.traffic_ratio.asc()
        return RoutingRow.traffic_ratio.desc()

    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RoutingRow.id.asc()
        return RoutingRow.id.desc()
