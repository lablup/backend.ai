from __future__ import annotations

from collections.abc import Collection

import sqlalchemy as sa

from ai.backend.common.identifier.replica_group import ReplicaGroupID
from ai.backend.manager.data.deployment.types import ReplicaGroupHandlerCategory
from ai.backend.manager.models.query_types import QueryCondition
from ai.backend.manager.models.replica_group_history.row import ReplicaGroupHistoryRow


class ReplicaGroupHistoryConditions:
    """Query conditions for replica group history."""

    @staticmethod
    def by_replica_group_ids(group_ids: Collection[ReplicaGroupID]) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.replica_group_id.in_(group_ids)

        return inner

    @staticmethod
    def by_category(category: ReplicaGroupHandlerCategory) -> QueryCondition:
        def inner() -> sa.sql.expression.ColumnElement[bool]:
            return ReplicaGroupHistoryRow.category == category

        return inner
