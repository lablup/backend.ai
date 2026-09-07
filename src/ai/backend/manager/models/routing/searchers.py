"""Searcher spec for the routings table."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, override

import sqlalchemy as sa

from ai.backend.manager.data.deployment.types import ModelReplicaData
from ai.backend.manager.models.routing.row import RoutingRow
from ai.backend.manager.models.specs.searcher import Searcher


@dataclass
class ModelReplicaSearcher(Searcher[RoutingRow, ModelReplicaData]):
    """Routing rows read as replicas."""

    @override
    def build_select(self) -> sa.sql.Select[Any]:
        return sa.select(RoutingRow)

    @override
    def to_data(self, row: RoutingRow) -> ModelReplicaData:
        return row.to_replica_data()
