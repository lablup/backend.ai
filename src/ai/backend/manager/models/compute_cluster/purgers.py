from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, override

from sqlalchemy.orm import InstrumentedAttribute

from ai.backend.common.data.entity.compute_cluster import ComputeClusterID
from ai.backend.common.data.entity.types import EntityIdentifier
from ai.backend.manager.data.compute_cluster.types import ComputeClusterData
from ai.backend.manager.models.compute_cluster.row import ComputeClusterRow
from ai.backend.manager.models.compute_cluster.searchable_fields import (
    ComputeClusterSearchableFields,
)
from ai.backend.manager.models.specs.purger import EntityPurger
from ai.backend.manager.models.specs.types import ConflictCheck


@dataclass
class ComputeClusterPurger(EntityPurger[ComputeClusterRow, ComputeClusterData]):
    """Purger for removing a compute cluster registration."""

    compute_cluster_id: ComputeClusterID

    @override
    def row_class(self) -> type[ComputeClusterRow]:
        return ComputeClusterRow

    @override
    def target_id_column(self) -> InstrumentedAttribute[Any]:
        return ComputeClusterRow.id

    @override
    def entity_id(self) -> EntityIdentifier:
        return self.compute_cluster_id

    @override
    def conflict_checks(self) -> Sequence[ConflictCheck]:
        return ()

    @override
    def to_data(self, row: ComputeClusterRow) -> ComputeClusterData:
        return ComputeClusterSearchableFields.own.to_data(row)
