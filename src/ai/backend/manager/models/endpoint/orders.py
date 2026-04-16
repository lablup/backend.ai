"""Query orders for endpoint models."""

from __future__ import annotations

from ai.backend.manager.models.endpoint import (
    EndpointAutoScalingRuleRow,
    EndpointRow,
    EndpointTokenRow,
)
from ai.backend.manager.repositories.base import QueryOrder


class DeploymentOrders:
    """Query orders for deployments."""

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return EndpointRow.name.asc()
        return EndpointRow.name.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return EndpointRow.created_at.asc()
        return EndpointRow.created_at.desc()

    @staticmethod
    def destroyed_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return EndpointRow.destroyed_at.asc()
        return EndpointRow.destroyed_at.desc()


class AccessTokenOrders:
    """Query orders for access tokens."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return EndpointTokenRow.created_at.asc()
        return EndpointTokenRow.created_at.desc()


class AutoScalingRuleOrders:
    """Query orders for auto-scaling rules."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return EndpointAutoScalingRuleRow.created_at.asc()
        return EndpointAutoScalingRuleRow.created_at.desc()
