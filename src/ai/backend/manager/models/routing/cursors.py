"""Paging replicas around the row a cursor names."""

from __future__ import annotations

import uuid

import sqlalchemy as sa

from ai.backend.manager.models.clauses import QueryCondition
from ai.backend.manager.models.routing.row import RoutingRow


class ReplicaCursor:
    """Reads the cursor row's ``created_at`` and takes the rows on one side of it."""

    def after(self, cursor_id: str) -> QueryCondition:
        return self._compare(cursor_id, forward=True)

    def before(self, cursor_id: str) -> QueryCondition:
        return self._compare(cursor_id, forward=False)

    def _compare(self, cursor_id: str, forward: bool) -> QueryCondition:
        replica_id = uuid.UUID(cursor_id)

        def inner() -> sa.sql.expression.ColumnElement[bool]:
            created_at = (
                sa.select(RoutingRow.created_at)
                .where(RoutingRow.id == replica_id)
                .scalar_subquery()
            )
            if forward:
                return RoutingRow.created_at < created_at
            return RoutingRow.created_at > created_at

        return inner
