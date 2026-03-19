"""Query orders for agent rows."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.dto.manager.v2.agent.types import AgentOrderField, OrderDirection
from ai.backend.manager.repositories.base import QueryOrder

from .row import AgentRow

_OrderColumn = sa.ColumnElement[Any] | InstrumentedAttribute[Any]

ORDER_FIELD_MAP: dict[AgentOrderField, _OrderColumn] = {
    AgentOrderField.ID: AgentRow.id,
    AgentOrderField.STATUS: AgentRow.status,
    AgentOrderField.RESOURCE_GROUP: AgentRow.scaling_group,
    AgentOrderField.FIRST_CONTACT: AgentRow.first_contact,
    AgentOrderField.SCHEDULABLE: AgentRow.schedulable,
}

DEFAULT_FORWARD_ORDER: QueryOrder = AgentRow.first_contact.desc()
DEFAULT_BACKWARD_ORDER: QueryOrder = AgentRow.first_contact.asc()
TIEBREAKER_ORDER: QueryOrder = AgentRow.id.asc()


class AgentOrders:
    """Order factories used by GQL AgentOrderByGQL.to_query_order()."""

    @staticmethod
    def id(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentRow.id.asc()
        return AgentRow.id.desc()

    @staticmethod
    def status(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentRow.status.asc()
        return AgentRow.status.desc()

    @staticmethod
    def scaling_group(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentRow.scaling_group.asc()
        return AgentRow.scaling_group.desc()

    @staticmethod
    def first_contact(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentRow.first_contact.asc()
        return AgentRow.first_contact.desc()

    @staticmethod
    def schedulable(ascending: bool = True) -> QueryOrder:
        if ascending:
            return AgentRow.schedulable.asc()
        return AgentRow.schedulable.desc()


def resolve_order(field: AgentOrderField, direction: OrderDirection) -> QueryOrder:
    """Resolve a DTO order field + direction to a SQLAlchemy order expression."""
    col = ORDER_FIELD_MAP[field]
    if direction == OrderDirection.DESC:
        return col.desc()
    return col.asc()
