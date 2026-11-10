"""What a replica-group history search can filter and order by, and how a row becomes data."""

from __future__ import annotations

from typing import override

from ai.backend.common.data.entity.replica_group_history import ReplicaGroupHistoryID
from ai.backend.manager.data.deployment.types import (
    ReplicaGroupHandlerCategory,
    ReplicaGroupHistoryData,
)
from ai.backend.manager.data.session.types import SchedulingResult
from ai.backend.manager.models.replica_group_history.row import ReplicaGroupHistoryRow
from ai.backend.manager.models.specs.conditions.datetime import DateTimeConditions
from ai.backend.manager.models.specs.conditions.enum import EnumConditions
from ai.backend.manager.models.specs.conditions.integer import IntConditions
from ai.backend.manager.models.specs.conditions.string import (
    StringConditions,
    StringEqualityConditions,
)
from ai.backend.manager.models.specs.conditions.uuid import UUIDConditions
from ai.backend.manager.models.specs.orders.column import ColumnOrder
from ai.backend.manager.models.specs.search.converter import RowDataConverter
from ai.backend.manager.models.specs.search.field import SearchableField


class _ReplicaGroupHistoryOwnFields(
    RowDataConverter[ReplicaGroupHistoryRow, ReplicaGroupHistoryData]
):
    """The history row's own columns.

    ``sub_steps`` is JSONB, so both slots stay empty; ``message`` is ``sa.Text`` with no
    index serving a partial match, so it carries equality and membership only.
    """

    id = SearchableField(
        ReplicaGroupHistoryRow.id,
        UUIDConditions(ReplicaGroupHistoryRow.id),
        ColumnOrder(ReplicaGroupHistoryRow.id),
    )
    replica_group_id = SearchableField(
        ReplicaGroupHistoryRow.replica_group_id,
        UUIDConditions(ReplicaGroupHistoryRow.replica_group_id),
        ColumnOrder(ReplicaGroupHistoryRow.replica_group_id),
    )
    deployment_id = SearchableField(
        ReplicaGroupHistoryRow.deployment_id,
        UUIDConditions(ReplicaGroupHistoryRow.deployment_id),
        ColumnOrder(ReplicaGroupHistoryRow.deployment_id),
    )
    category = SearchableField(
        ReplicaGroupHistoryRow.category,
        EnumConditions(ReplicaGroupHistoryRow.category, ReplicaGroupHandlerCategory),
        ColumnOrder(ReplicaGroupHistoryRow.category),
    )
    phase = SearchableField(
        ReplicaGroupHistoryRow.phase,
        StringConditions(ReplicaGroupHistoryRow.phase),
        ColumnOrder(ReplicaGroupHistoryRow.phase),
    )
    from_status = SearchableField(
        ReplicaGroupHistoryRow.from_status,
        StringConditions(ReplicaGroupHistoryRow.from_status),
        ColumnOrder(ReplicaGroupHistoryRow.from_status),
    )
    to_status = SearchableField(
        ReplicaGroupHistoryRow.to_status,
        StringConditions(ReplicaGroupHistoryRow.to_status),
        ColumnOrder(ReplicaGroupHistoryRow.to_status),
    )
    result = SearchableField(
        ReplicaGroupHistoryRow.result,
        EnumConditions(ReplicaGroupHistoryRow.result, SchedulingResult),
        ColumnOrder(ReplicaGroupHistoryRow.result),
    )
    error_code = SearchableField(
        ReplicaGroupHistoryRow.error_code,
        StringConditions(ReplicaGroupHistoryRow.error_code),
        ColumnOrder(ReplicaGroupHistoryRow.error_code),
    )
    message = SearchableField(
        ReplicaGroupHistoryRow.message,
        StringEqualityConditions(ReplicaGroupHistoryRow.message),
        None,
    )
    sub_steps = SearchableField(ReplicaGroupHistoryRow.sub_steps, None, None)
    attempts = SearchableField(
        ReplicaGroupHistoryRow.attempts,
        IntConditions(ReplicaGroupHistoryRow.attempts),
        ColumnOrder(ReplicaGroupHistoryRow.attempts),
    )
    created_at = SearchableField(
        ReplicaGroupHistoryRow.created_at,
        DateTimeConditions(ReplicaGroupHistoryRow.created_at),
        ColumnOrder(ReplicaGroupHistoryRow.created_at),
    )
    updated_at = SearchableField(
        ReplicaGroupHistoryRow.updated_at,
        DateTimeConditions(ReplicaGroupHistoryRow.updated_at),
        ColumnOrder(ReplicaGroupHistoryRow.updated_at),
    )

    @override
    def to_data(self, row: ReplicaGroupHistoryRow) -> ReplicaGroupHistoryData:
        return ReplicaGroupHistoryData(
            id=ReplicaGroupHistoryID(self.id.read(row)),
            replica_group_id=self.replica_group_id.read(row),
            deployment_id=self.deployment_id.read(row),
            category=self.category.read(row),
            phase=self.phase.read(row),
            from_status=self.from_status.read(row),
            to_status=self.to_status.read(row),
            result=SchedulingResult(self.result.read(row)),
            error_code=self.error_code.read(row),
            message=self.message.read(row),
            sub_steps=self.sub_steps.read(row),
            attempts=self.attempts.read(row),
            created_at=self.created_at.read(row),
            updated_at=self.updated_at.read(row),
        )


class ReplicaGroupHistorySearchableFields:
    own = _ReplicaGroupHistoryOwnFields()
