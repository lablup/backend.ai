from __future__ import annotations

from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.manager.data.deployment.types import ReplicaGroupData
from ai.backend.manager.models.replica_group.row import ReplicaGroupRow
from ai.backend.manager.models.replica_group.searchable_fields import (
    ReplicaGroupSearchableFields,
)
from ai.backend.manager.models.specs.querier import BulkFieldQuerier


class BulkReplicaGroupQuerier(BulkFieldQuerier[ReplicaGroupRow, ReplicaGroupData]):
    """The replica groups the caller named."""

    @override
    def row_class(self) -> type[ReplicaGroupRow]:
        return ReplicaGroupRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ReplicaGroupRow.id

    @override
    def to_data(self, row: ReplicaGroupRow) -> ReplicaGroupData:
        return ReplicaGroupSearchableFields.own.to_data(row)
