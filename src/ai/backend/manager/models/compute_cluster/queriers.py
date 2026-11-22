"""DataQuerier implementations for compute clusters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.compute_cluster import ComputeClusterID
from ai.backend.manager.data.compute_cluster.types import ComputeClusterData
from ai.backend.manager.models.compute_cluster.row import ComputeClusterRow
from ai.backend.manager.models.compute_cluster.searchable_fields import (
    ComputeClusterSearchableFields,
)
from ai.backend.manager.models.specs.querier import BulkEntityQuerier, DataQuerier


@dataclass
class ComputeClusterQuerier(DataQuerier[ComputeClusterRow, ComputeClusterData]):
    compute_cluster_id: ComputeClusterID

    @override
    def row_class(self) -> type[ComputeClusterRow]:
        return ComputeClusterRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return ComputeClusterRow.id

    @override
    def entity_id_value(self) -> ComputeClusterID:
        return self.compute_cluster_id

    @override
    def to_data(self, row: ComputeClusterRow) -> ComputeClusterData:
        return ComputeClusterSearchableFields.own.to_data(row)


class BulkComputeClusterQuerier(BulkEntityQuerier[ComputeClusterRow, ComputeClusterData]):
    """The compute clusters the caller named."""

    @override
    def row_class(self) -> type[ComputeClusterRow]:
        return ComputeClusterRow

    @override
    def entity_id_column(self) -> InstrumentedAttribute[Any]:
        return ComputeClusterRow.id

    @override
    def to_data(self, row: ComputeClusterRow) -> ComputeClusterData:
        return ComputeClusterSearchableFields.own.to_data(row)
