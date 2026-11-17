"""BulkFieldQuerier implementation for the replica-group history table."""

from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.deployment.types import ReplicaGroupHistoryData
from ai.backend.manager.models.replica_group_history.query_spec import (
    ReplicaGroupHistoryQuerySpec,
)
from ai.backend.manager.models.replica_group_history.row import ReplicaGroupHistoryRow
from ai.backend.manager.models.specs.querier import BulkFieldQuerier


class BulkReplicaGroupHistoryQuerier(
    BulkFieldQuerier[ReplicaGroupHistoryRow, ReplicaGroupHistoryData]
):
    """The replica-group history rows the caller named."""

    @override
    def row_class(self) -> type[ReplicaGroupHistoryRow]:
        return ReplicaGroupHistoryRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ReplicaGroupHistoryRow.id

    @override
    def to_data(self, row: ReplicaGroupHistoryRow) -> ReplicaGroupHistoryData:
        return ReplicaGroupHistoryQuerySpec.own.to_data(row)
