"""Query orders for vfolder rows."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.dto.manager.v2.vfolder.types import OrderDirection, VFolderOrderField
from ai.backend.manager.repositories.base import QueryOrder

from .row import VFolderRow

_OrderColumn = sa.ColumnElement[Any] | InstrumentedAttribute[Any]

ORDER_FIELD_MAP: dict[VFolderOrderField, _OrderColumn] = {
    VFolderOrderField.NAME: VFolderRow.name,
    VFolderOrderField.CREATED_AT: VFolderRow.created_at,
    VFolderOrderField.STATUS: VFolderRow.status,
    VFolderOrderField.USAGE_MODE: VFolderRow.usage_mode,
    VFolderOrderField.HOST: VFolderRow.host,
}

DEFAULT_FORWARD_ORDER: QueryOrder = VFolderRow.created_at.desc()
DEFAULT_BACKWARD_ORDER: QueryOrder = VFolderRow.created_at.asc()
TIEBREAKER_ORDER: QueryOrder = VFolderRow.id.asc()


class VFolderOrders:
    """Query orders for vfolders."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return VFolderRow.created_at.asc()
        return VFolderRow.created_at.desc()

    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return VFolderRow.id.asc()
        return VFolderRow.id.desc()

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return VFolderRow.name.asc()
        return VFolderRow.name.desc()

    @staticmethod
    def status(ascending: bool = True) -> QueryOrder:
        if ascending:
            return VFolderRow.status.asc()
        return VFolderRow.status.desc()

    @staticmethod
    def usage_mode(ascending: bool = True) -> QueryOrder:
        if ascending:
            return VFolderRow.usage_mode.asc()
        return VFolderRow.usage_mode.desc()

    @staticmethod
    def host(ascending: bool = True) -> QueryOrder:
        if ascending:
            return VFolderRow.host.asc()
        return VFolderRow.host.desc()


def resolve_order(field: VFolderOrderField, direction: OrderDirection) -> QueryOrder:
    """Resolve a DTO order field + direction to a SQLAlchemy order expression."""
    col = ORDER_FIELD_MAP[field]
    if direction == OrderDirection.DESC:
        return col.desc()
    return col.asc()
