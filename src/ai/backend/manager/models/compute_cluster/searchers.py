"""Searcher implementations for compute clusters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.compute_cluster.types import ComputeClusterData
from ai.backend.manager.models.compute_cluster.row import ComputeClusterRow
from ai.backend.manager.models.compute_cluster.searchable_fields import (
    ComputeClusterSearchableFields,
)
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ComputeClusterSearcher(Searcher[ComputeClusterRow, ComputeClusterData]):
    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(ComputeClusterRow)

    @override
    def to_data(self, row: ComputeClusterRow) -> ComputeClusterData:
        return ComputeClusterSearchableFields.own.to_data(row)
