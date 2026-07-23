"""Query orders for replica group history rows."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.dto.manager.v2.scheduling_history.types import (
    OrderDirection,
    ReplicaGroupHistoryOrderField,
)
from ai.backend.manager.models.clauses import QueryOrder
from ai.backend.manager.models.replica_group_history.row import ReplicaGroupHistoryRow

_OrderColumn = sa.ColumnElement[Any] | InstrumentedAttribute[Any]

REPLICA_GROUP_ORDER_FIELD_MAP: dict[ReplicaGroupHistoryOrderField, _OrderColumn] = {
    ReplicaGroupHistoryOrderField.CREATED_AT: ReplicaGroupHistoryRow.created_at,
    ReplicaGroupHistoryOrderField.UPDATED_AT: ReplicaGroupHistoryRow.updated_at,
    ReplicaGroupHistoryOrderField.PHASE: ReplicaGroupHistoryRow.phase,
    ReplicaGroupHistoryOrderField.FROM_STATUS: ReplicaGroupHistoryRow.from_status,
    ReplicaGroupHistoryOrderField.TO_STATUS: ReplicaGroupHistoryRow.to_status,
    ReplicaGroupHistoryOrderField.RESULT: ReplicaGroupHistoryRow.result,
    ReplicaGroupHistoryOrderField.ATTEMPTS: ReplicaGroupHistoryRow.attempts,
}

REPLICA_GROUP_DEFAULT_FORWARD_ORDER: QueryOrder = ReplicaGroupHistoryRow.created_at.desc()
REPLICA_GROUP_DEFAULT_BACKWARD_ORDER: QueryOrder = ReplicaGroupHistoryRow.created_at.asc()
REPLICA_GROUP_TIEBREAKER_ORDER: QueryOrder = ReplicaGroupHistoryRow.id.asc()


def resolve_replica_group_order(
    field: ReplicaGroupHistoryOrderField, direction: OrderDirection
) -> QueryOrder:
    """Resolve a DTO order field + direction to a SQLAlchemy order expression."""
    col = REPLICA_GROUP_ORDER_FIELD_MAP[field]
    if direction == OrderDirection.DESC:
        return col.desc()
    return col.asc()
