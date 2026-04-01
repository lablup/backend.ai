"""Query orders for session rows."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.dto.manager.v2.session.types import OrderDirection, SessionOrderField
from ai.backend.manager.repositories.base import QueryOrder

from .row import SessionRow

_OrderColumn = sa.ColumnElement[Any] | InstrumentedAttribute[Any]

ORDER_FIELD_MAP: dict[SessionOrderField, _OrderColumn] = {
    SessionOrderField.CREATED_AT: SessionRow.created_at,
    SessionOrderField.TERMINATED_AT: SessionRow.terminated_at,
    SessionOrderField.STATUS: SessionRow.status,
    SessionOrderField.ID: SessionRow.id,
    SessionOrderField.NAME: SessionRow.name,
}

DEFAULT_FORWARD_ORDER: QueryOrder = SessionRow.created_at.desc()
DEFAULT_BACKWARD_ORDER: QueryOrder = SessionRow.created_at.asc()
TIEBREAKER_ORDER: QueryOrder = SessionRow.id.asc()


class SessionOrders:
    """Query orders for sessions."""

    @staticmethod
    def created_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return SessionRow.created_at.asc()
        return SessionRow.created_at.desc()

    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return SessionRow.id.asc()
        return SessionRow.id.desc()

    @staticmethod
    def terminated_at(ascending: bool = True) -> QueryOrder:
        if ascending:
            return SessionRow.terminated_at.asc()
        return SessionRow.terminated_at.desc()

    @staticmethod
    def status(ascending: bool = True) -> QueryOrder:
        if ascending:
            return SessionRow.status.asc()
        return SessionRow.status.desc()

    @staticmethod
    def name(ascending: bool = True) -> QueryOrder:
        if ascending:
            return SessionRow.name.asc()
        return SessionRow.name.desc()


def resolve_order(field: SessionOrderField, direction: OrderDirection) -> QueryOrder:
    """Resolve a DTO order field + direction to a SQLAlchemy order expression."""
    col = ORDER_FIELD_MAP[field]
    if direction == OrderDirection.DESC:
        return col.desc()
    return col.asc()
