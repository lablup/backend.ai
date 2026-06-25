"""Query orders for endpoint models."""

from __future__ import annotations

from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.endpoint import (
    EndpointAutoScalingRuleRow,
    EndpointRow,
    EndpointTokenRow,
)


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

    @staticmethod
    def domain(ascending: bool = True) -> QueryOrder:
        if ascending:
            return EndpointRow.domain.asc()
        return EndpointRow.domain.desc()

    @staticmethod
    def project(ascending: bool = True) -> QueryOrder:
        if ascending:
            return EndpointRow.project.asc()
        return EndpointRow.project.desc()

    @staticmethod
    def resource_group(ascending: bool = True) -> QueryOrder:
        if ascending:
            return EndpointRow.resource_group.asc()
        return EndpointRow.resource_group.desc()

    @staticmethod
    def tag(ascending: bool = True) -> QueryOrder:
        if ascending:
            return EndpointRow.tag.asc()
        return EndpointRow.tag.desc()


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
