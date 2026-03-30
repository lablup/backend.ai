"""Query orders for kernel rows."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.dto.manager.v2.kernel.types import KernelOrderField, OrderDirection
from ai.backend.manager.repositories.base import QueryOrder

from .row import KernelRow

_OrderColumn = sa.ColumnElement[Any] | InstrumentedAttribute[Any]

ORDER_FIELD_MAP: dict[KernelOrderField, _OrderColumn] = {
    KernelOrderField.CLUSTER_IDX: KernelRow.cluster_idx,
    KernelOrderField.CREATED_AT: KernelRow.created_at,
    KernelOrderField.TERMINATED_AT: KernelRow.terminated_at,
    KernelOrderField.STATUS: KernelRow.status,
    KernelOrderField.CLUSTER_MODE: KernelRow.cluster_mode,
    KernelOrderField.CLUSTER_HOSTNAME: KernelRow.cluster_hostname,
}

DEFAULT_FORWARD_ORDER: QueryOrder = KernelRow.created_at.desc()
DEFAULT_BACKWARD_ORDER: QueryOrder = KernelRow.created_at.asc()
TIEBREAKER_ORDER: QueryOrder = KernelRow.id.asc()


class KernelOrders:
    """Query orders for kernels."""

    @staticmethod
    def cluster_idx(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KernelRow.cluster_idx.asc()
        return KernelRow.cluster_idx.desc()

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KernelRow.created_at.asc()
        return KernelRow.created_at.desc()

    @staticmethod
    def terminated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KernelRow.terminated_at.asc()
        return KernelRow.terminated_at.desc()

    @staticmethod
    def status(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KernelRow.status.asc()
        return KernelRow.status.desc()

    @staticmethod
    def cluster_mode(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KernelRow.cluster_mode.asc()
        return KernelRow.cluster_mode.desc()

    @staticmethod
    def cluster_hostname(ascending: bool = True) -> QueryOrder:
        if ascending:
            return KernelRow.cluster_hostname.asc()
        return KernelRow.cluster_hostname.desc()


def resolve_order(field: KernelOrderField, direction: OrderDirection) -> QueryOrder:
    """Resolve a DTO order field + direction to a SQLAlchemy order expression."""
    col = ORDER_FIELD_MAP[field]
    if direction == OrderDirection.DESC:
        return col.desc()
    return col.asc()
