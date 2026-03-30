"""Query orders for scheduling history rows."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.dto.manager.v2.scheduling_history.types import (
    DeploymentHistoryOrderField,
    OrderDirection,
    RouteHistoryOrderField,
    SessionHistoryOrderField,
)
from ai.backend.manager.repositories.base import QueryOrder

from .row import (
    DeploymentHistoryRow,
    KernelSchedulingHistoryRow,
    RouteHistoryRow,
    SessionSchedulingHistoryRow,
)

_OrderColumn = sa.ColumnElement[Any] | InstrumentedAttribute[Any]


# ========== Session Scheduling History ==========

SESSION_ORDER_FIELD_MAP: dict[SessionHistoryOrderField, _OrderColumn] = {
    SessionHistoryOrderField.CREATED_AT: SessionSchedulingHistoryRow.created_at,
    SessionHistoryOrderField.UPDATED_AT: SessionSchedulingHistoryRow.updated_at,
}

SESSION_DEFAULT_FORWARD_ORDER: QueryOrder = SessionSchedulingHistoryRow.created_at.desc()
SESSION_DEFAULT_BACKWARD_ORDER: QueryOrder = SessionSchedulingHistoryRow.created_at.asc()
SESSION_TIEBREAKER_ORDER: QueryOrder = SessionSchedulingHistoryRow.id.asc()


class SessionSchedulingHistoryOrders:
    """Order factories used by GQL SessionSchedulingHistoryOrderBy.to_query_order()."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return SessionSchedulingHistoryRow.created_at.asc()
        return SessionSchedulingHistoryRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return SessionSchedulingHistoryRow.updated_at.asc()
        return SessionSchedulingHistoryRow.updated_at.desc()


def resolve_session_order(field: SessionHistoryOrderField, direction: OrderDirection) -> QueryOrder:
    """Resolve a DTO order field + direction to a SQLAlchemy order expression."""
    col = SESSION_ORDER_FIELD_MAP[field]
    if direction == OrderDirection.DESC:
        return col.desc()
    return col.asc()


# ========== Kernel Scheduling History ==========


class KernelSchedulingHistoryOrders:
    """Order factories used by GQL KernelSchedulingHistoryOrderBy.to_query_order()."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KernelSchedulingHistoryRow.created_at.asc()
        return KernelSchedulingHistoryRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KernelSchedulingHistoryRow.updated_at.asc()
        return KernelSchedulingHistoryRow.updated_at.desc()


# ========== Deployment History ==========

DEPLOYMENT_ORDER_FIELD_MAP: dict[DeploymentHistoryOrderField, _OrderColumn] = {
    DeploymentHistoryOrderField.CREATED_AT: DeploymentHistoryRow.created_at,
    DeploymentHistoryOrderField.UPDATED_AT: DeploymentHistoryRow.updated_at,
}

DEPLOYMENT_DEFAULT_FORWARD_ORDER: QueryOrder = DeploymentHistoryRow.created_at.desc()
DEPLOYMENT_DEFAULT_BACKWARD_ORDER: QueryOrder = DeploymentHistoryRow.created_at.asc()
DEPLOYMENT_TIEBREAKER_ORDER: QueryOrder = DeploymentHistoryRow.id.asc()


class DeploymentHistoryOrders:
    """Order factories used by GQL DeploymentHistoryOrderBy.to_query_order()."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DeploymentHistoryRow.created_at.asc()
        return DeploymentHistoryRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return DeploymentHistoryRow.updated_at.asc()
        return DeploymentHistoryRow.updated_at.desc()


def resolve_deployment_order(
    field: DeploymentHistoryOrderField, direction: OrderDirection
) -> QueryOrder:
    """Resolve a DTO order field + direction to a SQLAlchemy order expression."""
    col = DEPLOYMENT_ORDER_FIELD_MAP[field]
    if direction == OrderDirection.DESC:
        return col.desc()
    return col.asc()


# ========== Route History ==========

ROUTE_ORDER_FIELD_MAP: dict[RouteHistoryOrderField, _OrderColumn] = {
    RouteHistoryOrderField.CREATED_AT: RouteHistoryRow.created_at,
    RouteHistoryOrderField.UPDATED_AT: RouteHistoryRow.updated_at,
}

ROUTE_DEFAULT_FORWARD_ORDER: QueryOrder = RouteHistoryRow.created_at.desc()
ROUTE_DEFAULT_BACKWARD_ORDER: QueryOrder = RouteHistoryRow.created_at.asc()
ROUTE_TIEBREAKER_ORDER: QueryOrder = RouteHistoryRow.id.asc()


class RouteHistoryOrders:
    """Order factories used by GQL RouteHistoryOrderBy.to_query_order()."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RouteHistoryRow.created_at.asc()
        return RouteHistoryRow.created_at.desc()

    @staticmethod
    def updated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return RouteHistoryRow.updated_at.asc()
        return RouteHistoryRow.updated_at.desc()


def resolve_route_order(field: RouteHistoryOrderField, direction: OrderDirection) -> QueryOrder:
    """Resolve a DTO order field + direction to a SQLAlchemy order expression."""
    col = ROUTE_ORDER_FIELD_MAP[field]
    if direction == OrderDirection.DESC:
        return col.desc()
    return col.asc()
